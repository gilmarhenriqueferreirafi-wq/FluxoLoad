from __future__ import annotations

import atexit
import gc
import os
from pathlib import Path
import shutil
import tempfile
import time
from typing import Callable

from .pot_provider import ensure_pot_provider


class DownloadError(RuntimeError):
    """Erro amigável para a camada de interface."""


def _cleanup_cookie_file(cookie_file: str | None) -> None:
    if not cookie_file:
        return
    path = Path(cookie_file)
    gc.collect()
    for _ in range(25):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(0.2)
    def cleanup_at_exit() -> None:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

    atexit.register(cleanup_at_exit)


class DownloadManager:
    """Interface pequena para baixar uma URL usando o adaptador disponível."""

    def download(
        self,
        url: str,
        destination: Path,
        progress: Callable[[dict], None],
        options: dict | None = None,
    ) -> Path:
        try:
            import yt_dlp
        except ImportError as error:
            raise DownloadError(
                "A dependência yt-dlp não está instalada. "
                "Execute: py -m pip install -r requirements.txt"
            ) from error

        destination.mkdir(parents=True, exist_ok=True)
        work_destination = destination / ".fluxoload_work"
        work_destination.mkdir(parents=True, exist_ok=True)
        last_path: Path | None = None

        def hook(data: dict) -> None:
            nonlocal last_path
            status = data.get("status")
            if status == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes", 0)
                percent = (downloaded / total * 100) if total else 0
                progress(
                    {
                        "percent": percent,
                        "text": f"{percent:.1f}% — {data.get('filename', '')}",
                    }
                )
            elif status == "finished":
                last_path = Path(data.get("filename", ""))
                progress({"percent": 99, "text": "Processando arquivo..."})

        download_options = options or {}
        ensure_pot_provider()
        ffmpeg_path = self._find_ffmpeg()
        media_type = download_options.get("media_type", "video")
        quality = download_options.get("quality", "Melhor disponível")
        height = {"1080p": 1080, "720p": 720, "480p": 480, "360p": 360}.get(quality)
        height_filter = f"[height<={height}]" if height else ""
        language = download_options.get("audio_language", "original")
        language_filter = f"[language^={language}]" if language != "original" else ""
        if media_type == "audio":
            selected_format = f"bestaudio{language_filter}/bestaudio/best"
        elif ffmpeg_path:
            selected_format = (
                f"bestvideo[ext=mp4][vcodec^=avc1]{height_filter}+"
                f"bestaudio[ext=m4a][acodec^=mp4a]{language_filter}/"
                f"best[ext=mp4]{height_filter}/best{height_filter}"
            )
        else:
            selected_format = f"best[ext=mp4]{height_filter}/best{height_filter}"

        options = {
            # H.264 + AAC tem compatibilidade ampla no Windows e em celulares.
            # Sem FFmpeg, baixar um único arquivo evita o erro de merge.
            "format": selected_format,
            # Arquivos intermediários ficam fora da pasta visível de downloads.
            "outtmpl": str(work_destination / "%(title)s [%(id)s] [compat].%(ext)s"),
            "noplaylist": True,
            "windowsfilenames": True,
            "overwrites": False,
            "continuedl": False,
            "progress_hooks": [hook],
            "quiet": True,
            "no_warnings": True,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 5,
            "socket_timeout": 30,
            "concurrent_fragment_downloads": 1,
            "js_runtimes": {"node": {}},
            "extractor_args": {
                # Permite fallback quando o mweb recebe LOGIN_REQUIRED antes
                # de chegar à etapa de geração do PO Token.
                "youtube": {"player_client": ["mweb", "tv", "web_safari"]},
                # extractor_args usa listas para argumentos nomeados do plugin.
                "youtubepot-bgutilhttp": {"base_url": ["http://127.0.0.1:4416"]},
            },
        }
        user_agent = download_options.get("user_agent")
        if user_agent:
            options["http_headers"] = {
                "User-Agent": user_agent,
                "Referer": "https://www.youtube.com/",
            }
        if ffmpeg_path:
            options["ffmpeg_location"] = ffmpeg_path
            options["merge_output_format"] = "mp4"
        if media_type == "audio":
            audio_quality = {
                "320 kbps": "320",
                "256 kbps": "256",
                "192 kbps": "192",
                "128 kbps": "128",
                "Padrão (recomendado)": "192",
            }.get(quality, "192")
            options["postprocessors"] = [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": audio_quality,
                }
            ]
        if download_options.get("subtitles") and media_type == "video":
            options["writesubtitles"] = True
            options["writeautomaticsub"] = True
            options["subtitleslangs"] = [download_options.get("subtitle_language", "pt")]
            options["subtitlesformat"] = "srt/best"
            options["embedsubs"] = bool(ffmpeg_path)
        cookie_file = download_options.get("cookiefile")
        browser_profile = download_options.get("browser_profile")
        browser_cookie_jar = None
        if browser_profile and not cookie_file:
            try:
                from yt_dlp.cookies import extract_cookies_from_browser

                class SilentCookieLogger:
                    def debug(self, *args, **kwargs):
                        pass

                    info = debug
                    warning = debug
                    error = debug

                cookie_jar = extract_cookies_from_browser(
                    "chromium", browser_profile, SilentCookieLogger()
                )
                browser_cookie_jar = cookie_jar
            except Exception:
                browser_cookie_jar = None
        if cookie_file:
            options["cookiefile"] = cookie_file

        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                if browser_cookie_jar is not None:
                    ydl.cookiejar = browser_cookie_jar
                info = ydl.extract_info(url, download=True)
                prepared = Path(info.get("filepath") or ydl.prepare_filename(info))
        except Exception as error:
            message = str(error)
            if "WinError 32" in message or "sendo usado por outro processo" in message:
                message = (
                    "O Windows bloqueou o arquivo porque ele está sendo usado por outro processo. "
                    "Feche o vídeo, o Explorador de Arquivos ou o player e tente novamente.\n\n"
                    + message
                )
            elif "getaddrinfo failed" in message or "Failed to resolve" in message:
                message = (
                    "A conexão com o servidor de vídeo falhou na resolução DNS. "
                    "O FluxoLoad tentou novamente, mas a rede não respondeu. "
                    "Verifique a internet, VPN ou DNS e tente outra vez.\n\n"
                    + message
                )
            raise DownloadError(message) from error
        finally:
            try:
                del ydl
            except UnboundLocalError:
                pass
            _cleanup_cookie_file(cookie_file)

        candidates = [prepared]
        if prepared.suffix.lower() != ".mp4":
            candidates.append(prepared.with_suffix(".mp4"))
        if media_type == "audio":
            candidates.append(prepared.with_suffix(".mp3"))
        if last_path and last_path not in candidates:
            candidates.append(last_path)

        final_source = next((path for path in candidates if path.exists()), None)
        if final_source is None:
            raise DownloadError("O download terminou, mas o arquivo final não foi localizado.")

        final_path = destination / final_source.name
        if final_path.exists():
            final_path = destination / f"{final_source.stem} (novo){final_source.suffix}"
        shutil.move(str(final_source), str(final_path))
        return final_path

    @staticmethod
    def _find_ffmpeg() -> str | None:
        """Procura FFmpeg no PATH e na pasta herdada do projeto antigo."""
        from_path = shutil.which("ffmpeg")
        if from_path:
            return from_path

        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            old_project_path = (
                Path(local_app_data) / "DownloaderUniversal" / "ffmpeg" / "bin" / "ffmpeg.exe"
            )
            if old_project_path.is_file():
                return str(old_project_path)

        return None
