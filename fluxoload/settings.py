from __future__ import annotations

import json
from pathlib import Path


class AppSettings:
    """Preferências locais do usuário, sem servidor ou telemetria."""

    DEFAULTS = {
        "download_directory": str(Path.home() / "Downloads" / "FluxoLoad"),
        "media_type": "video",
        "quality": "Melhor disponível",
        "audio_language": "original",
        "subtitles": False,
        "subtitle_language": "pt",
        "open_after_download": False,
        "open_download_panel": True,
        "theme": "Claro",
        "accent_color": "#ff0033",
    }

    def __init__(self, values: dict | None = None) -> None:
        self.values = dict(self.DEFAULTS)
        if values:
            self.values.update(values)

    @property
    def path(self) -> Path:
        return Path.home() / "AppData" / "Local" / "FluxoLoad" / "settings.json"

    @classmethod
    def load(cls) -> "AppSettings":
        settings = cls()
        try:
            if settings.path.is_file():
                settings.values.update(json.loads(settings.path.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
        return settings

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.values, ensure_ascii=False, indent=2), encoding="utf-8"
        )
