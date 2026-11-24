from __future__ import annotations

import base64
import os
import subprocess
import sys
from pathlib import Path


def create_first_run_shortcuts(project_root: Path) -> None:
    """Create app launch shortcuts once, without replacing user-customized links."""
    if sys.platform != "win32":
        return

    project_root = project_root.resolve()
    entry_point = project_root / "run.py"
    if not entry_point.is_file():
        return

    python_exe = Path(sys.executable)
    pythonw = python_exe.with_name("pythonw.exe")
    if not pythonw.is_file():
        pythonw = python_exe

    icon = project_root / "assets" / "fluxoload-icon.ico"
    script = r'''
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')
$paths = @($env:FLUXOLOAD_SHORTCUT_ROOT, (Join-Path $desktop 'FluxoLoad.lnk'))
foreach ($path in $paths) {
    if ([string]::IsNullOrWhiteSpace($path) -or (Test-Path -LiteralPath $path)) { continue }
    $link = $shell.CreateShortcut($path)
    $link.TargetPath = $env:FLUXOLOAD_SHORTCUT_PYTHON
    $link.Arguments = '"' + $env:FLUXOLOAD_SHORTCUT_ENTRY + '"'
    $link.WorkingDirectory = $env:FLUXOLOAD_SHORTCUT_WORKDIR
    if (Test-Path -LiteralPath $env:FLUXOLOAD_SHORTCUT_ICON) {
        $link.IconLocation = $env:FLUXOLOAD_SHORTCUT_ICON + ',0'
    }
    $link.Description = 'Iniciar FluxoLoad'
    $link.Save()
}
'''
    encoded_script = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    environment = os.environ.copy()
    environment.update(
        {
            "FLUXOLOAD_SHORTCUT_ROOT": str(project_root / "FluxoLoad.lnk"),
            "FLUXOLOAD_SHORTCUT_PYTHON": str(pythonw),
            "FLUXOLOAD_SHORTCUT_ENTRY": str(entry_point),
            "FLUXOLOAD_SHORTCUT_WORKDIR": str(project_root),
            "FLUXOLOAD_SHORTCUT_ICON": str(icon),
        }
    )
    startup_info = subprocess.STARTUPINFO()
    startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup_info.wShowWindow = 0
    try:
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded_script,
            ],
            env=environment,
            startupinfo=startup_info,
            creationflags=subprocess.CREATE_NO_WINDOW,
            check=False,
            timeout=15,
        )
    except (OSError, subprocess.SubprocessError):
        pass
