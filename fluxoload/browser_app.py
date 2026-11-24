from __future__ import annotations

import sys
import os
import ctypes
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFileDialog,
    QColorDialog,
    QLabel,
    QLineEdit,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QDockWidget,
    QFrame,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import QSize
from PySide6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineScript
from PySide6.QtWebEngineWidgets import QWebEngineView

from .downloader import DownloadError, DownloadManager
from .pot_provider import ensure_pot_provider
from .settings import AppSettings
from .shortcuts import create_first_run_shortcuts
from .theme import build_stylesheet


class DownloadOptionsDialog(QDialog):
    def __init__(self, parent=None, defaults: dict | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Opções do download")
        self.setMinimumWidth(360)

        form = QFormLayout(self)
        self.media_type = QComboBox()
        self.media_type.addItems(["Vídeo", "Áudio"])
        self.quality = QComboBox()
        self.media_type.setItemData(0, "video")
        self.media_type.setItemData(1, "audio")
        self.quality_hint = QLabel()
        self.quality_hint.setObjectName("mutedLabel")
        self.quality.addItems(["Melhor disponível", "1080p", "720p", "480p", "360p"])
        self.audio_language = QComboBox()
        self.audio_language.addItem("Original", "original")
        self.audio_language.addItem("Português", "pt")
        self.audio_language.addItem("Inglês", "en")
        self.audio_language.addItem("Espanhol", "es")
        self.subtitles = QCheckBox("Baixar legendas")
        self.subtitle_language = QComboBox()
        self.subtitle_language.addItem("Português", "pt")
        self.subtitle_language.addItem("Inglês", "en")
        self.subtitle_language.addItem("Espanhol", "es")
        self.subtitle_language.addItem("Português e inglês", "pt,en")
        self.media_type.currentTextChanged.connect(self._update_audio_state)
        self.media_type.currentIndexChanged.connect(self._update_quality_options)
        form.addRow("Tipo:", self.media_type)
        form.addRow("Qualidade:", self.quality)
        form.addRow("", self.quality_hint)
        form.addRow("Idioma do áudio:", self.audio_language)
        form.addRow(self.subtitles)
        form.addRow("Idioma da legenda:", self.subtitle_language)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)
        defaults = defaults or {}
        self.media_type.setCurrentText("Áudio" if defaults.get("media_type") == "audio" else "Vídeo")
        self.quality.setCurrentText(defaults.get("quality", "Melhor disponível"))
        audio_index = self.audio_language.findData(defaults.get("audio_language", "original"))
        if audio_index >= 0:
            self.audio_language.setCurrentIndex(audio_index)
        self.subtitles.setChecked(bool(defaults.get("subtitles", False)))
        subtitle_index = self.subtitle_language.findData(defaults.get("subtitle_language", "pt"))
        if subtitle_index >= 0:
            self.subtitle_language.setCurrentIndex(subtitle_index)
        self._update_audio_state(self.media_type.currentText())

    def _update_audio_state(self, media_type: str) -> None:
        is_audio = media_type == "Áudio"
        self.subtitles.setEnabled(not is_audio)
        self.subtitle_language.setEnabled(not is_audio)

    def _update_quality_options(self) -> None:
        current = self.quality.currentText()
        is_audio = self.media_type.currentData() == "audio"
        values = (["Padrão (recomendado)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"]
                  if is_audio else ["Melhor disponível", "1080p", "720p", "480p", "360p"])
        self.quality.blockSignals(True)
        self.quality.clear()
        self.quality.addItems(values)
        default_value = "Padrão (recomendado)" if is_audio else "Melhor disponível"
        self.quality.setCurrentText(current if current in values else default_value)
        self.quality_hint.setText(
            "Padrão: MP3 192 kbps, bom equilíbrio entre qualidade e tamanho."
            if is_audio
            else "Escolha a resolução máxima do vídeo."
        )
        self.quality.blockSignals(False)

    def values(self) -> dict:
        return {
            "media_type": "audio" if self.media_type.currentText() == "Áudio" else "video",
            "quality": self.quality.currentText(),
            "audio_language": self.audio_language.currentData(),
            "subtitles": self.subtitles.isChecked(),
            "subtitle_language": self.subtitle_language.currentData(),
        }


class DownloadWorker(QObject):
    progress = Signal(dict)
    completed = Signal(str)
    failed = Signal(str)

    def __init__(self, url: str, destination: str, options: dict) -> None:
        super().__init__()
        self.url = url
        self.destination = destination
        self.options = options

    @Slot()
    def run(self) -> None:
        try:
            result = DownloadManager().download(
                self.url,
                Path(self.destination),
                progress=self.progress.emit,
                options=self.options,
            )
        except DownloadError as error:
            self.failed.emit(str(error))
            return
        except Exception as error:
            self.failed.emit(f"Falha inesperada ({type(error).__name__}): {error}")
            return
        self.completed.emit(str(result))


class QuietWebView(QWebEngineView):
    """Não repassa ao terminal avisos internos do JavaScript das plataformas."""

    def __init__(self, profile: QWebEngineProfile) -> None:
        super().__init__()
        self.setPage(QWebEnginePage(profile, self))
        script = QWebEngineScript()
        script.setName("fluxoload-hide-youtube-shorts")
        script.setInjectionPoint(QWebEngineScript.InjectionPoint.DocumentReady)
        script.setWorldId(QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        script.setSourceCode(
            """
            (() => {
              if (!location.hostname.endsWith('youtube.com')) return;
              const style = document.createElement('style');
              style.textContent = `
                a[href*='/shorts/'],
                ytd-reel-shelf-renderer,
                ytm-reel-shelf-renderer,
                ytd-rich-section-renderer:has(a[href*='/shorts/']),
                ytd-video-renderer:has(a[href*='/shorts/']),
                ytd-rich-item-renderer:has(a[href*='/shorts/']),
                ytd-grid-video-renderer:has(a[href*='/shorts/']) {
                  display: none !important;
                }
              `;
              document.documentElement.appendChild(style);
              const removeShorts = () => {
                document.querySelectorAll('a[href*="/shorts/"]').forEach((link) => {
                  const item = link.closest(
                    'ytd-rich-item-renderer, ytd-video-renderer, ytd-grid-video-renderer, ytd-reel-shelf-renderer'
                  );
                  if (item) item.style.display = 'none';
                });
                document.querySelectorAll('a, yt-formatted-string').forEach((node) => {
                  if (node.textContent.trim().toLowerCase() === 'shorts') {
                    const item = node.closest('ytd-guide-entry-renderer, tp-yt-paper-item, a');
                    if (item) item.style.display = 'none';
                  }
                });
              };
              removeShorts();
              new MutationObserver(removeShorts).observe(document.documentElement, {
                childList: true,
                subtree: true
              });
            })();
            """
        )
        self.page().scripts().insert(script)

    def javaScriptConsoleMessage(self, level, message, line, source):
        return


class BrowserFluxoLoadApp(QObject):
    PLATFORMS = {
        "YouTube": "https://www.youtube.com",
        "Instagram": "https://www.instagram.com",
        "TikTok": "https://www.tiktok.com",
    }

    def __init__(self) -> None:
        super().__init__()
        chromium_flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")
        if "--disable-features=WebGPU" not in chromium_flags:
            os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
                f"{chromium_flags} --disable-features=WebGPU"
            ).strip()
        self.qt_app = QApplication(sys.argv)
        icon_path = Path(__file__).resolve().parent.parent / "assets" / "fluxoload-icon.ico"
        if not icon_path.is_file():
            icon_path = Path(__file__).resolve().parent.parent / "assets" / "fluxoload-icon.png"
        app_icon = QIcon(str(icon_path)) if icon_path.is_file() else QIcon()
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "FluxoLoad.Desktop.Application"
                )
            except (AttributeError, OSError):
                pass
        if not app_icon.isNull():
            self.qt_app.setWindowIcon(app_icon)
        self.settings = AppSettings.load()
        self.qt_app.setStyleSheet(
            build_stylesheet(self.settings.values["theme"], self.settings.values["accent_color"])
        )
        self.window = QMainWindow()
        self.window.setWindowTitle("FluxoLoad")
        if not app_icon.isNull():
            self.window.setWindowIcon(app_icon)
        self._native_taskbar_icon = None
        if sys.platform == "win32" and icon_path.suffix.lower() == ".ico":
            try:
                user32 = ctypes.windll.user32
                user32.LoadImageW.argtypes = [
                    ctypes.c_void_p,
                    ctypes.c_wchar_p,
                    ctypes.c_uint,
                    ctypes.c_int,
                    ctypes.c_int,
                    ctypes.c_uint,
                ]
                user32.LoadImageW.restype = ctypes.c_void_p
                user32.SendMessageW.argtypes = [
                    ctypes.c_void_p,
                    ctypes.c_uint,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                ]
                user32.SendMessageW.restype = ctypes.c_void_p
                native_icon = user32.LoadImageW(
                    None,
                    str(icon_path),
                    1,  # IMAGE_ICON
                    0,
                    0,
                    0x00000010 | 0x00000040,  # LR_LOADFROMFILE | LR_DEFAULTSIZE
                )
                if native_icon:
                    self._native_taskbar_icon = native_icon
                    hwnd = int(self.window.winId())
                    user32.SendMessageW(hwnd, 0x0080, 0, native_icon)  # WM_SETICON, ICON_SMALL
                    user32.SendMessageW(hwnd, 0x0080, 1, native_icon)  # WM_SETICON, ICON_BIG
            except (AttributeError, OSError, TypeError, ValueError):
                self._native_taskbar_icon = None
        self.window.resize(1180, 760)
        self.destination = Path(self.settings.values["download_directory"])
        profile_dir = Path.home() / "AppData" / "Local" / "FluxoLoad" / "browser-profile"
        self.browser_profile_dir = profile_dir
        cache_dir = profile_dir / "cache"
        profile_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)
        self.web_profile = QWebEngineProfile("FluxoLoadProfile", self.qt_app)
        self.web_profile.setPersistentStoragePath(str(profile_dir))
        self.web_profile.setCachePath(str(cache_dir))
        self.web_profile.setPersistentCookiesPolicy(
            QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
        )
        self.browser = QuietWebView(self.web_profile)
        self.browser_cookie_store = self.web_profile.cookieStore()
        self._browser_cookies = {}
        self.browser_cookie_store.cookieAdded.connect(self._cache_browser_cookie)
        self.browser_cookie_store.loadAllCookies()
        self.stack = QStackedWidget()
        self.home = QWidget()
        self._settings_return_index = 0
        self._settings_return_widget = self.home
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.detail = QLabel("Pronto para navegar")
        self.status = QStatusBar()
        self.worker: DownloadWorker | None = None
        self.download_thread: QThread | None = None
        self.download_dock: QDockWidget | None = None
        self.download_panel_layout: QVBoxLayout | None = None
        self.download_scroll_area: QScrollArea | None = None
        self.download_filter: QComboBox | None = None
        self.download_row_progress: QProgressBar | None = None
        self.download_row_status: QLabel | None = None
        self._active_download_row: QFrame | None = None
        self._last_download_url: str | None = None
        self._last_download_options: dict | None = None
        self._download_queue: list[
            tuple[str, dict, tuple[QFrame, QProgressBar, QLabel] | None]
        ] = []
        self._download_in_progress = False
        self._last_session_diagnostic = "Sessão ainda não sincronizada"
        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = QToolBar("Navegação")
        toolbar.setMovable(False)
        self.window.addToolBar(toolbar)
        logo = QLabel("FluxoLoad")
        logo.setObjectName("appLogo")
        toolbar.addWidget(logo)

        for label, callback in (
            ("⌂ Home", self.show_home),
            ("←", self.browser.back),
            ("→", self.browser.forward),
            ("↻", self.browser.reload),
        ):
            button = QPushButton(label)
            button.setObjectName("iconButton")
            button.clicked.connect(callback)
            toolbar.addWidget(button)

        download = QPushButton("Baixar video atual")
        download.setObjectName("primaryButton")
        download.clicked.connect(self.download_current_page)
        toolbar.addWidget(download)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        downloads = QPushButton("Downloads")
        downloads.setObjectName("iconButton")
        downloads.clicked.connect(self.toggle_download_panel)
        toolbar.addWidget(downloads)

        settings_button = QPushButton("⚙")
        settings_button.setToolTip("Configurações")
        settings_button.setFixedWidth(42)
        settings_button.clicked.connect(self.show_settings)
        toolbar.addWidget(settings_button)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        self._build_home()
        self.stack.addWidget(self.home)
        self.stack.addWidget(self.browser)
        layout.addWidget(self.stack, stretch=1)
        layout.addWidget(self.progress)
        layout.addWidget(self.detail)
        self.main_stack = QStackedWidget()
        self.main_stack.addWidget(central)
        self.main_stack.addWidget(self._build_settings_page())
        self.window.setCentralWidget(self.main_stack)
        self.window.setStatusBar(self.status)
        self._build_download_panel()

        self.browser.loadStarted.connect(lambda: self.status.showMessage("Carregando página..."))
        self.browser.loadFinished.connect(self._load_finished)

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 30, 36, 30)
        title = QLabel("Configurações do FluxoLoad")
        title.setStyleSheet("font-size: 24px; font-weight: 600;")
        layout.addWidget(title)
        form = QFormLayout()

        self.settings_directory = QLineEdit(str(self.destination))
        choose = QPushButton("Escolher")
        choose.clicked.connect(self.choose_settings_directory)
        directory_row = QHBoxLayout()
        directory_row.addWidget(self.settings_directory)
        directory_row.addWidget(choose)
        form.addRow("Diretório de downloads:", directory_row)

        self.settings_media_type = QComboBox()
        self.settings_media_type.addItem("Vídeo", "video")
        self.settings_media_type.addItem("Áudio", "audio")
        self.settings_media_type.setCurrentIndex(
            1 if self.settings.values["media_type"] == "audio" else 0
        )
        form.addRow("Tipo padrão:", self.settings_media_type)

        self.settings_quality = QComboBox()
        self.settings_quality.addItems(["Melhor disponível", "1080p", "720p", "480p", "360p"])
        self.settings_quality.setCurrentText(self.settings.values["quality"])
        form.addRow("Qualidade padrão:", self.settings_quality)
        self.settings_media_type.currentIndexChanged.connect(self.update_settings_quality_options)
        self.update_settings_quality_options()

        self.settings_audio_language = QComboBox()
        for label, value in (("Original", "original"), ("Português", "pt"), ("Inglês", "en"), ("Espanhol", "es")):
            self.settings_audio_language.addItem(label, value)
        index = self.settings_audio_language.findData(self.settings.values["audio_language"])
        if index >= 0:
            self.settings_audio_language.setCurrentIndex(index)
        form.addRow("Idioma preferido do áudio:", self.settings_audio_language)

        self.settings_subtitles = QCheckBox("Baixar legendas por padrão")
        self.settings_subtitles.setChecked(bool(self.settings.values["subtitles"]))
        form.addRow(self.settings_subtitles)

        self.settings_subtitle_language = QComboBox()
        for label, value in (("Português", "pt"), ("Inglês", "en"), ("Espanhol", "es"), ("Português e inglês", "pt,en")):
            self.settings_subtitle_language.addItem(label, value)
        index = self.settings_subtitle_language.findData(self.settings.values["subtitle_language"])
        if index >= 0:
            self.settings_subtitle_language.setCurrentIndex(index)
        form.addRow("Idioma padrão das legendas:", self.settings_subtitle_language)

        self.settings_open_after = QCheckBox("Abrir o arquivo automaticamente ao concluir")
        self.settings_open_after.setChecked(bool(self.settings.values["open_after_download"]))
        form.addRow(self.settings_open_after)

        self.settings_open_download_panel = QCheckBox(
            "Abrir o painel de Downloads ao iniciar um download"
        )
        self.settings_open_download_panel.setChecked(
            bool(self.settings.values.get("open_download_panel", True))
        )
        form.addRow(self.settings_open_download_panel)

        self.settings_theme = QComboBox()
        self.settings_theme.addItems(["Claro", "Escuro"])
        self.settings_theme.setCurrentText(self.settings.values.get("theme", "Claro"))
        form.addRow("Tema:", self.settings_theme)

        self.settings_accent = QLineEdit(self.settings.values.get("accent_color", "#ff0033"))
        choose_accent = QPushButton("Escolher cor")
        choose_accent.clicked.connect(self.choose_accent_color)
        accent_row = QHBoxLayout()
        accent_row.addWidget(self.settings_accent)
        accent_row.addWidget(choose_accent)
        form.addRow("Cor de destaque:", accent_row)
        layout.addLayout(form)
        actions = QHBoxLayout()
        save = QPushButton("Salvar configurações")
        save.clicked.connect(self.save_settings)
        reset = QPushButton("Restaurar padrões")
        reset.clicked.connect(self.reset_settings)
        actions.addWidget(save)
        actions.addWidget(reset)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def show_settings(self) -> None:
        if self.main_stack.currentIndex() == 1:
            self.main_stack.setCurrentIndex(self._settings_return_index)
            if self._settings_return_index == 0:
                self.stack.setCurrentWidget(self._settings_return_widget)
            return

        self._settings_return_index = self.main_stack.currentIndex()
        if self._settings_return_index == 0:
            self._settings_return_widget = self.stack.currentWidget()
        self.main_stack.setCurrentIndex(1)

    def choose_settings_directory(self) -> None:
        selected = QFileDialog.getExistingDirectory(self.window, "Escolher diretório", str(self.destination))
        if selected:
            self.settings_directory.setText(selected)

    def update_settings_quality_options(self) -> None:
        current = self.settings_quality.currentText()
        is_audio = self.settings_media_type.currentData() == "audio"
        values = (["Padrão (recomendado)", "320 kbps", "256 kbps", "192 kbps", "128 kbps"]
                  if is_audio else ["Melhor disponível", "1080p", "720p", "480p", "360p"])
        self.settings_quality.blockSignals(True)
        self.settings_quality.clear()
        self.settings_quality.addItems(values)
        default_value = "Padrão (recomendado)" if is_audio else "Melhor disponível"
        self.settings_quality.setCurrentText(current if current in values else default_value)
        self.settings_quality.blockSignals(False)

    def choose_accent_color(self) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            self.settings_accent.setText(color.name())

    def save_settings(self) -> None:
        self.settings.values.update(
            {
                "download_directory": self.settings_directory.text().strip(),
                "media_type": self.settings_media_type.currentData(),
                "quality": self.settings_quality.currentText(),
                "audio_language": self.settings_audio_language.currentData(),
                "subtitles": self.settings_subtitles.isChecked(),
                "subtitle_language": self.settings_subtitle_language.currentData(),
                "open_after_download": self.settings_open_after.isChecked(),
                "open_download_panel": self.settings_open_download_panel.isChecked(),
                "theme": self.settings_theme.currentText(),
                "accent_color": self.settings_accent.text().strip() or "#ff0033",
            }
        )
        self.settings.save()
        self.qt_app.setStyleSheet(
            build_stylesheet(self.settings.values["theme"], self.settings.values["accent_color"])
        )
        self._refresh_platform_icons()
        self.destination = Path(self.settings.values["download_directory"])
        self.refresh_download_files()
        self.status.showMessage("Configurações salvas")

    def reset_settings(self) -> None:
        defaults = AppSettings.DEFAULTS
        self.settings_directory.setText(defaults["download_directory"])
        self.settings_media_type.setCurrentIndex(0)
        self.settings_quality.setCurrentText(defaults["quality"])
        self.settings_audio_language.setCurrentIndex(
            self.settings_audio_language.findData(defaults["audio_language"])
        )
        self.settings_subtitles.setChecked(defaults["subtitles"])
        self.settings_subtitle_language.setCurrentIndex(
            self.settings_subtitle_language.findData(defaults["subtitle_language"])
        )
        self.settings_open_after.setChecked(defaults["open_after_download"])
        self.settings_open_download_panel.setChecked(defaults["open_download_panel"])
        self.settings_theme.setCurrentText(defaults["theme"])
        self.settings_accent.setText(defaults["accent_color"])
        self.status.showMessage("Padrões carregados; clique em Salvar configurações para confirmar")

    def _build_home(self) -> None:
        home_layout = QVBoxLayout(self.home)
        home_layout.setContentsMargins(20, 40, 20, 40)
        home_layout.setSpacing(12)

        title = QLabel("Escolha uma plataforma")
        title.setObjectName("homeTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(title)

        subtitle = QLabel("Pesquise e baixe vídeos localmente")
        subtitle.setObjectName("homeSubtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_layout.addWidget(subtitle)

        row = QHBoxLayout()
        row.setSpacing(28)
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.platform_buttons = {}
        for name, address in self.PLATFORMS.items():
            cell = QVBoxLayout()
            cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button = QPushButton()
            button.setObjectName("platformButton")
            button.setFixedSize(136, 136)
            self.platform_buttons[name] = button
            if not self._set_platform_icon(button, name):
                button.setText("♪")
                button.setStyleSheet(
                    "QPushButton { border: none; background: #111827; color: white; "
                    "border-radius: 68px; font-size: 42px; font-weight: bold; }"
                )
            button.clicked.connect(lambda _checked=False, url=address: self.open_platform(url))
            label = QLabel(name)
            label.setObjectName("platformLabel")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.addWidget(button, alignment=Qt.AlignmentFlag.AlignCenter)
            cell.addWidget(label)
            row.addLayout(cell)
        home_layout.addStretch(1)
        home_layout.addLayout(row)
        home_layout.addStretch(2)

    def _platform_resource_dir(self) -> Path:
        resource_roots = [
            Path(getattr(sys, "_MEIPASS", "")) / "assets",
            Path(__file__).resolve().parent.parent / "assets",
            Path.cwd() / "assets",
        ]
        return next((path for path in resource_roots if path.is_dir()), resource_roots[1])

    def _platform_icon_path(self, name: str) -> Path:
        suffix = "escuro" if self.settings.values.get("theme") == "Escuro" else "claro"
        base_name = {"YouTube": "youtube", "Instagram": "instagram", "TikTok": "tiktok"}[name]
        resource_dir = self._platform_resource_dir()
        themed = resource_dir / f"{base_name}_{suffix}.png"
        if themed.is_file():
            return themed
        fallback = resource_dir / f"{base_name}.png"
        if fallback.is_file():
            return fallback
        return resource_dir / f"{base_name}.webp"

    def _set_platform_icon(self, button: QPushButton, name: str) -> bool:
        image_path = self._platform_icon_path(name)
        if not image_path.is_file():
            return False
        button.setIcon(QIcon(str(image_path)))
        button.setIconSize(QSize(124, 124))
        return True

    def _refresh_platform_icons(self) -> None:
        for name, button in getattr(self, "platform_buttons", {}).items():
            self._set_platform_icon(button, name)

    def _load_finished(self, success: bool) -> None:
        self.status.showMessage("Página carregada" if success else "Falha ao carregar página")

    def open_platform(self, address: str) -> None:
        self.main_stack.setCurrentIndex(0)
        self.stack.setCurrentWidget(self.browser)
        self.browser.setUrl(QUrl(address))

    def show_home(self) -> None:
        self.main_stack.setCurrentIndex(0)
        self.stack.setCurrentWidget(self.home)

    def _build_download_panel(self) -> None:
        self.download_dock = QDockWidget("Downloads", self.window)
        self.download_dock.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.download_dock.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.download_dock.setMinimumWidth(260)
        self.download_dock.setMaximumWidth(600)
        self.download_dock.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred
        )
        self.download_dock.setVisible(False)
        panel = QWidget()
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        actions = QHBoxLayout()
        self.download_filter = QComboBox()
        self.download_filter.addItem("Todos", "all")
        self.download_filter.addItem("Vídeos (.mp4)", "video")
        self.download_filter.addItem("Áudios (.mp3)", "audio")
        self.download_filter.currentIndexChanged.connect(self.refresh_download_files)
        actions.addWidget(self.download_filter)
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh_download_files)
        open_folder = QPushButton("Abrir diretório")
        open_folder.clicked.connect(self.open_download_directory)
        actions.addWidget(refresh)
        actions.addWidget(open_folder)
        panel_layout.addLayout(actions)

        scroll_content = QWidget()
        self.download_panel_layout = QVBoxLayout(scroll_content)
        self.download_panel_layout.setContentsMargins(0, 0, 0, 0)
        empty = QLabel("Nenhum download iniciado")
        empty.setObjectName("emptyDownloads")
        self.download_panel_layout.addWidget(empty)
        self.download_panel_layout.addStretch(1)
        self.download_scroll_area = QScrollArea()
        self.download_scroll_area.setWidgetResizable(True)
        self.download_scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.download_scroll_area.setWidget(scroll_content)
        panel_layout.addWidget(self.download_scroll_area, stretch=1)
        self.download_dock.setWidget(panel)
        self.window.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.download_dock)
        self.refresh_download_files()

    def toggle_download_panel(self) -> None:
        if self.download_dock is not None:
            self._set_download_panel_visible(not self.download_dock.isVisible())

    def _set_download_panel_visible(self, visible: bool) -> None:
        if self.download_dock is None:
            return
        self.download_dock.setVisible(visible)
        if visible:
            self.refresh_download_files()
        show_global_progress = not visible and self._download_in_progress
        self.progress.setVisible(show_global_progress)
        self.detail.setVisible(show_global_progress)

    def open_download_directory(self) -> None:
        self.destination.mkdir(parents=True, exist_ok=True)
        import os

        os.startfile(self.destination)

    def refresh_download_files(self) -> None:
        if self.download_panel_layout is None or self.download_dock is None:
            return
        panel = self.download_dock.widget()
        empty = panel.findChild(QLabel, "emptyDownloads")
        for row in panel.findChildren(QFrame, "existingDownload"):
            row.deleteLater()
        selected_filter = self.download_filter.currentData() if self.download_filter else "all"
        files = sorted(
            (
                file
                for file in self.destination.glob("*")
                if file.is_file()
                and file.suffix.lower() in {".mp4", ".mp3"}
                and (
                    selected_filter == "all"
                    or (selected_filter == "video" and file.suffix.lower() == ".mp4")
                    or (selected_filter == "audio" and file.suffix.lower() == ".mp3")
                )
            ),
            key=lambda file: file.stat().st_mtime,
            reverse=True,
        )
        if empty is not None:
            empty.setVisible(not files)
        for file in files:
            row = QFrame()
            row.setObjectName("existingDownload")
            row.setFrameShape(QFrame.Shape.StyledPanel)
            row_layout = QVBoxLayout(row)
            row_layout.setContentsMargins(10, 8, 10, 8)
            name = QLabel(file.name)
            name.setWordWrap(True)
            size_mb = file.stat().st_size / (1024 * 1024)
            info = QLabel(f"Arquivo local • {size_mb:.1f} MB")
            info.setObjectName("mutedLabel")
            open_file = QPushButton("Abrir")
            open_file.clicked.connect(lambda _checked=False, path=file: self.open_file(path))
            row_layout.addWidget(name)
            row_layout.addWidget(info)
            row_layout.addWidget(open_file)
            self.download_panel_layout.insertWidget(
                max(1, self.download_panel_layout.count() - 1), row
            )

    @staticmethod
    def open_file(path: Path) -> None:
        import os

        if path.is_file():
            os.startfile(path)

    def _create_download_row(
        self, url: str, status_text: str = "Preparando download..."
    ) -> tuple[QFrame, QProgressBar, QLabel] | None:
        if self.download_dock is None:
            return None
        panel = self.download_dock.widget()
        layout = self.download_panel_layout
        if layout is None:
            return None
        empty = panel.findChild(QLabel, "emptyDownloads")
        if empty is not None:
            empty.hide()
        row = QFrame()
        row.setObjectName("activeDownload")
        row.setFrameShape(QFrame.Shape.StyledPanel)
        row_layout = QVBoxLayout(row)
        row_layout.setContentsMargins(10, 10, 10, 10)
        title = QLabel(url)
        title.setWordWrap(True)
        title.setMinimumWidth(0)
        title.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        progress = QProgressBar()
        status = QLabel(status_text)
        status.setObjectName("mutedLabel")
        row_layout.addWidget(title)
        row_layout.addWidget(progress)
        row_layout.addWidget(status)
        layout.insertWidget(max(0, layout.count() - 1), row)
        return row, progress, status

    def _add_download_row(self, url: str) -> None:
        created = self._create_download_row(url)
        if created is None:
            return
        _, progress, status = created
        self.download_row_progress = progress
        self.download_row_status = status
        self._active_download_row = created[0]
        if self.settings.values.get("open_download_panel", True):
            self._set_download_panel_visible(True)

    def _export_browser_cookies(self, callback) -> None:
        """Exporta cookies da sessão local em formato temporário para o yt-dlp."""
        store = self.browser_cookie_store
        cookies = dict(self._browser_cookies)

        def value_text(value) -> str:
            try:
                return bytes(value).decode("utf-8", errors="replace")
            except TypeError:
                return str(value)

        def collect(cookie) -> None:
            key = (value_text(cookie.domain()), value_text(cookie.path()), value_text(cookie.name()))
            cookies[key] = cookie
            self._browser_cookies[key] = cookie

        store.cookieAdded.connect(collect)
        store.loadAllCookies()

        def finish() -> None:
            try:
                store.cookieAdded.disconnect(collect)
            except (TypeError, RuntimeError):
                pass
            if not cookies:
                callback(None, 0, False)
                return
            cookie_path = Path.home() / "AppData" / "Local" / "FluxoLoad" / "browser-cookies.txt"
            cookie_path.parent.mkdir(parents=True, exist_ok=True)
            with cookie_path.open("w", encoding="utf-8") as file:
                file.write("# Netscape HTTP Cookie File\n")
                for cookie in cookies.values():
                    domain = value_text(cookie.domain())
                    path = value_text(cookie.path()) or "/"
                    name = value_text(cookie.name())
                    value = value_text(cookie.value())
                    include_subdomains = "TRUE" if domain.startswith(".") else "FALSE"
                    secure = "TRUE" if cookie.isSecure() else "FALSE"
                    expiration = cookie.expirationDate()
                    expiry = expiration.toSecsSinceEpoch() if expiration.isValid() else 0
                    if cookie.isHttpOnly():
                        domain = f"#HttpOnly_{domain}"
                    file.write(
                        f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expiry}\t{name}\t{value}\n"
                    )
            auth_cookie_names = {
                "SID", "HSID", "SSID", "APISID", "SAPISID", "LOGIN_INFO",
                "__Secure-1PSID", "__Secure-3PSID", "__Secure-1PSIDTS",
                "__Secure-3PSIDTS", "SIDCC", "__Secure-1PSIDCC", "__Secure-3PSIDCC",
            }
            has_auth_cookie = any(
                value_text(cookie.name()) in auth_cookie_names
                and "youtube.com" in value_text(cookie.domain()).lower()
                for cookie in cookies.values()
            )
            callback(str(cookie_path), len(cookies), has_auth_cookie)

        QTimer.singleShot(2500, finish)

    def _cache_browser_cookie(self, cookie) -> None:
        def value_text(value) -> str:
            try:
                return bytes(value).decode("utf-8", errors="replace")
            except TypeError:
                return str(value)

        key = (value_text(cookie.domain()), value_text(cookie.path()), value_text(cookie.name()))
        self._browser_cookies[key] = cookie

    def _start_download(self, url: str, options: dict, cookie_path: str | None) -> None:
        if cookie_path:
            options["cookiefile"] = cookie_path
        options["browser_profile"] = str(self.browser_profile_dir)
        options["user_agent"] = self.web_profile.httpUserAgent()
        self.worker = DownloadWorker(url, str(self.destination), options)
        self.download_thread = QThread(self.window)
        self.worker.moveToThread(self.download_thread)
        self.worker.progress.connect(self._update_progress)
        self.worker.completed.connect(self._download_completed)
        self.worker.failed.connect(self._download_failed)
        self.worker.completed.connect(self.download_thread.quit)
        self.worker.failed.connect(self.download_thread.quit)
        self.worker.completed.connect(self.worker.deleteLater)
        self.worker.failed.connect(self.worker.deleteLater)
        self.download_thread.finished.connect(self.download_thread.deleteLater)
        self.download_thread.started.connect(self.worker.run)
        self.download_thread.start()

    def _start_next_queued_download(self) -> None:
        if self._download_in_progress or not self._download_queue:
            return
        if self.download_thread is not None and self.download_thread.isRunning():
            QTimer.singleShot(100, self._start_next_queued_download)
            return
        url, options, created_row = self._download_queue.pop(0)
        self._last_download_url = url
        self._last_download_options = dict(options)
        self._download_in_progress = True
        self.destination.mkdir(parents=True, exist_ok=True)
        if created_row is None:
            self._add_download_row(url)
        else:
            row, progress, status = created_row
            status.setText("Preparando download...")
            self.download_row_progress = progress
            self.download_row_status = status
            self._active_download_row = row
        if self.download_dock is None or not self.download_dock.isVisible():
            self.progress.setVisible(True)
            self.detail.setVisible(True)
        self.progress.setValue(0)
        self.detail.setText("Preparando download...")
        self.status.showMessage(
            f"Iniciando download da fila ({len(self._download_queue)} restante(s))",
            5000,
        )
        self._start_download_with_browser_cookies(url, options)

    def _start_download_with_browser_cookies(self, url: str, options: dict) -> None:
        self.detail.setText("Sincronizando sessão do navegador...")
        if self.download_row_status is not None:
            self.download_row_status.setText("Sincronizando sessão do navegador...")
        def start(cookie_path: str | None, cookie_count: int, has_auth_cookie: bool) -> None:
            provider_ready = ensure_pot_provider()
            if cookie_count:
                provider_text = "PO Token local ativo" if provider_ready else "PO Token local indisponível"
                message = f"Sessão sincronizada ({cookie_count} cookies) — {provider_text}"
                if not has_auth_cookie:
                    message += "; login do YouTube não detectado no navegador interno"
            else:
                message = "Nenhum cookie da sessão interna foi encontrado"
                if provider_ready:
                    message += " — PO Token local ativo"
                else:
                    message += " — PO Token local indisponível"
            self._last_session_diagnostic = message
            self.status.showMessage(message, 8000)
            if self.download_row_status is not None:
                self.download_row_status.setText("Preparando download...")
            self._start_download(url, options, cookie_path)

        self._export_browser_cookies(start)

    def _retry_last_download(self) -> None:
        if not self._last_download_url or self._last_download_options is None:
            return
        self._download_in_progress = True
        if self.download_dock is None or not self.download_dock.isVisible():
            self.progress.setVisible(True)
            self.detail.setVisible(True)
        self.progress.setValue(0)
        self.detail.setText("Tentando novamente...")
        if self.download_row_progress is not None:
            self.download_row_progress.setValue(0)
        if self.download_row_status is not None:
            self.download_row_status.setText("Tentando novamente...")
        self._start_download_with_browser_cookies(
            self._last_download_url, dict(self._last_download_options)
        )

    @Slot()
    def download_current_page(self) -> None:
        if self._download_in_progress and False:
            self.status.showMessage("Já existe um download em andamento; aguarde a conclusão.", 5000)
            QMessageBox.information(
                self.window,
                "Download em andamento",
                "Aguarde o download atual terminar antes de iniciar outro."
            )
            return

        url = self.browser.url().toString()
        if not url.startswith(("http://", "https://")):
            QMessageBox.warning(self.window, "URL inválida", "Abra uma página ou cole um link primeiro.")
            return

        if not self._is_supported_platform(self.browser.url().host()):
            QMessageBox.warning(
                self.window,
                "Site não suportado",
                "O FluxoLoad baixa vídeos somente das plataformas disponíveis nos botões.",
            )
            return

        if self._is_youtube_short(self.browser.url()):
            QMessageBox.information(
                self.window,
                "YouTube Shorts não suportado",
                "O FluxoLoad baixa vídeos normais do YouTube, mas não Shorts.",
            )
            return

        dialog = DownloadOptionsDialog(self.window, self.settings.values)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        options = dialog.values()
        if self._download_in_progress:
            queued_row = self._create_download_row(url, "Na fila...")
            self._download_queue.append((url, options, queued_row))
            self.status.showMessage(
                f"Download adicionado Ã  fila ({len(self._download_queue)} na fila)",
                5000,
            )
            return
        self._last_download_url = url
        self._last_download_options = dict(options)
        self._download_in_progress = True
        self.destination.mkdir(parents=True, exist_ok=True)
        self._add_download_row(url)
        if self.download_dock is None or not self.download_dock.isVisible():
            self.progress.setVisible(True)
            self.detail.setVisible(True)
        self.progress.setValue(0)
        self.detail.setText("Preparando download...")
        self._start_download_with_browser_cookies(url, options)

    def _is_supported_platform(self, host: str) -> bool:
        host = host.lower().removeprefix("www.")
        supported_hosts = {
            "youtube.com",
            "youtu.be",
            "instagram.com",
            "tiktok.com",
        }
        return any(host == domain or host.endswith("." + domain) for domain in supported_hosts)

    @staticmethod
    def _is_youtube_short(url: QUrl) -> bool:
        host = url.host().lower().removeprefix("www.")
        return host in {"youtube.com", "m.youtube.com"} and url.path().lower().startswith("/shorts/")

    @Slot(dict)
    def _update_progress(self, data: dict) -> None:
        percent = int(data.get("percent", 0))
        self.progress.setValue(max(0, min(percent, 100)))
        self.detail.setText(data.get("text", "Baixando..."))
        if self.download_row_progress is not None:
            self.download_row_progress.setValue(max(0, min(percent, 100)))
        if self.download_row_status is not None:
            self.download_row_status.setText(data.get("text", "Baixando..."))

    @Slot(str)
    def _download_completed(self, path: str) -> None:
        self._download_in_progress = False
        self.progress.setValue(100)
        self.progress.setVisible(False)
        self.detail.setVisible(False)
        self.detail.setText(f"Concluído: {Path(path).name}")
        if self._active_download_row is not None:
            self._active_download_row.setParent(None)
            self._active_download_row.deleteLater()
            self._active_download_row = None
        self.download_row_progress = None
        self.download_row_status = None
        self.status.showMessage("Download concluído")
        if self.download_row_progress is not None:
            self.download_row_progress.setValue(100)
        if self.download_row_status is not None:
            self.download_row_status.setText(f"Concluído: {Path(path).name}")
        self.refresh_download_files()
        if self.settings.values.get("open_after_download"):
            self.open_file(Path(path))
        QTimer.singleShot(0, self._start_next_queued_download)

    @Slot(str)
    def _download_failed(self, error: str) -> None:
        self._download_in_progress = False
        self.status.showMessage("Falha no download")
        self.detail.setText(self._last_session_diagnostic)
        if self.download_row_status is not None:
            self.download_row_status.setText("Falha no download")
        dialog = QMessageBox(self.window)
        dialog.setIcon(QMessageBox.Icon.Critical)
        dialog.setWindowTitle("Erro no download")
        dialog.setText(f"{error}\n\nDiagnóstico da sessão: {self._last_session_diagnostic}")
        dialog.setStandardButtons(
            QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close
        )
        retry_button = dialog.button(QMessageBox.StandardButton.Retry)
        close_button = dialog.button(QMessageBox.StandardButton.Close)
        retry_button.setText("Tentar novamente")
        close_button.setText("Sair")
        dialog.setDefaultButton(QMessageBox.StandardButton.Retry)
        dialog.exec()
        if dialog.standardButton(dialog.clickedButton()) == QMessageBox.StandardButton.Retry:
            self._retry_last_download()
        else:
            QTimer.singleShot(0, self._start_next_queued_download)

    def run(self) -> None:
        create_first_run_shortcuts(Path(__file__).resolve().parent.parent)
        self.window.show()
        if sys.platform == "win32" and self._native_taskbar_icon:
            hwnd = int(self.window.winId())
            user32 = ctypes.windll.user32
            user32.SendMessageW(hwnd, 0x0080, 0, self._native_taskbar_icon)
            user32.SendMessageW(hwnd, 0x0080, 1, self._native_taskbar_icon)
        sys.exit(self.qt_app.exec())
