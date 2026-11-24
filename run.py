import faulthandler
from pathlib import Path

if __name__ == "__main__":
    log_directory = Path.home() / "AppData" / "Local" / "FluxoLoad"
    log_directory.mkdir(parents=True, exist_ok=True)
    log_path = log_directory / "runtime-crash.log"
    with log_path.open("a", encoding="utf-8", buffering=1) as log_file:
        faulthandler.enable(log_file, all_threads=True)
        from fluxoload.browser_app import BrowserFluxoLoadApp

        BrowserFluxoLoadApp().run()
