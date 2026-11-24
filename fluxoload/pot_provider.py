from __future__ import annotations

import atexit
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from urllib.error import URLError
from urllib.request import urlopen


_provider_process: subprocess.Popen | None = None


def _provider_is_running() -> bool:
    try:
        with urlopen("http://127.0.0.1:4416/ping", timeout=0.5) as response:
            return response.status < 500
    except (OSError, URLError):
        return False


def ensure_pot_provider() -> bool:
    """Inicia o provedor local se ele estiver instalado na máquina."""
    global _provider_process
    if _provider_is_running():
        return True
    if _provider_process is not None and _provider_process.poll() is None:
        return False

    bundled_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    server_home = os.environ.get("FLUXOLOAD_BGUTIL_SERVER")
    candidates = [
        Path(server_home) if server_home else None,
        bundled_root / "third_party" / "bgutil-ytdlp-pot-provider" / "server",
        Path.home() / "bgutil-ytdlp-pot-provider" / "server",
        Path(__file__).resolve().parent.parent / "third_party" / "bgutil-ytdlp-pot-provider" / "server",
    ]
    server = next(
        (
            path
            for path in candidates
            if path is not None and (path / "build" / "main.js").is_file()
        ),
        None,
    )
    node_candidates = [
        os.environ.get("FLUXOLOAD_NODE"),
        str(bundled_root / "third_party" / "node" / "node.exe"),
        shutil.which("node"),
    ]
    node = next(
        (candidate for candidate in node_candidates if candidate and Path(candidate).is_file()),
        None,
    )
    if server is None or node is None:
        return False

    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    _provider_process = subprocess.Popen(
        [node, "build/main.js", "--host", "127.0.0.1", "--port", "4416"],
        cwd=server,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=flags,
    )
    for _ in range(10):
        if _provider_is_running():
            return True
        time.sleep(0.2)
    return False


@atexit.register
def _stop_pot_provider() -> None:
    if _provider_process is not None and _provider_process.poll() is None:
        _provider_process.terminate()
