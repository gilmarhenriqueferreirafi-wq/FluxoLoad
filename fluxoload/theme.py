from __future__ import annotations


def build_stylesheet(theme: str, accent: str) -> str:
    dark = theme == "Escuro"
    background = "#15171a" if dark else "#f4f6f8"
    surface = "#202328" if dark else "#ffffff"
    text = "#f3f4f6" if dark else "#202124"
    muted = "#aeb4bd" if dark else "#6b7280"
    border = "#3a4048" if dark else "#d8dde5"
    return f"""
        QMainWindow, QWidget {{ background: {background}; color: {text}; }}
        QToolBar {{ background: {surface}; border: none; padding: 6px; spacing: 6px; }}
        QLabel#appLogo {{ color: {accent}; font-size: 17px; font-weight: 700; padding: 0 8px; }}
        QToolButton, QPushButton {{
            background: {surface}; color: {text}; border: 1px solid {border};
            border-radius: 7px; padding: 7px 12px;
        }}
        QPushButton:hover {{ border-color: {accent}; background: {accent}; color: white; }}
        QPushButton#primaryButton {{ background: {accent}; color: white; border-color: {accent}; font-weight: 600; }}
        QPushButton#primaryButton:hover {{ background: {text}; color: {accent}; }}
        QPushButton#iconButton {{ min-width: 34px; padding: 7px; font-size: 15px; }}
        QTabBar::tab {{ background: {surface}; color: {muted}; padding: 9px 18px; }}
        QTabBar::tab:selected {{ color: {accent}; border-bottom: 2px solid {accent}; }}
        QTabWidget::pane {{ border: 1px solid {border}; border-radius: 8px; }}
        QDockWidget {{ titlebar-close-icon: none; border: 1px solid {border}; }}
        QMainWindow::separator {{ background: {border}; width: 6px; height: 6px; }}
        QMainWindow::separator:hover {{ background: {accent}; }}
        QLineEdit, QComboBox {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 7px; border-radius: 6px; }}
        QProgressBar {{ border: 1px solid {border}; border-radius: 5px; text-align: center; color: {text}; }}
        QProgressBar::chunk {{ background: {accent}; border-radius: 4px; }}
        QStatusBar {{ background: {surface}; color: {muted}; }}
        QLabel#homeTitle {{ color: {text}; font-size: 26px; font-weight: 600; }}
        QLabel#homeSubtitle, QLabel#mutedLabel, QLabel#emptyDownloads {{ color: {muted}; }}
        QLabel#platformLabel {{ color: {text}; font-size: 15px; font-weight: 600; }}
        QFrame#existingDownload, QFrame#activeDownload {{ background: {surface}; border: 1px solid {border}; border-radius: 8px; }}
        QPushButton#platformButton {{ border: none; background: transparent; padding: 0; }}
        QPushButton#platformButton:hover {{ border: 2px solid {accent}; border-radius: 68px; }}
    """
