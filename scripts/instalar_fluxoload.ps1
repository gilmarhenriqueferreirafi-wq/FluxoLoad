param(
    [Parameter(Mandatory = $true)][string]$SourceRoot,
    [Parameter(Mandatory = $true)][string]$PythonExe
)

$ErrorActionPreference = 'Stop'
$log = Join-Path $env:TEMP 'FluxoLoad-install.log'
try { Stop-Transcript -ErrorAction SilentlyContinue | Out-Null } catch {}
Start-Transcript -LiteralPath $log -Force | Out-Null
trap {
    $message = $_ | Out-String
    try { Stop-Transcript | Out-Null } catch {}
    try { $message | Add-Content -LiteralPath $log -Encoding UTF8 } catch {}
    exit 1
}
$source = (Resolve-Path -LiteralPath $SourceRoot).Path.TrimEnd('\')
$install = Join-Path $env:ProgramFiles 'FluxoLoad'
$uninstallKey = 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\FluxoLoad'
$systemDrive = Get-PSDrive -Name $env:SystemDrive.TrimEnd(':')

if ($systemDrive.Free -lt 1GB) {
    throw "Espaco insuficiente no disco $($env:SystemDrive). Libere pelo menos 1 GB e tente novamente."
}

if (-not (Test-Path -LiteralPath (Join-Path $source 'run.py'))) { throw 'run.py nao encontrado no pacote.' }
if (-not (Test-Path -LiteralPath $PythonExe)) { throw 'Python nao encontrado.' }
if ($source -eq $install.TrimEnd('\')) { throw 'A origem nao pode ser a pasta de instalacao.' }

New-Item -ItemType Directory -Path $install -Force | Out-Null
& robocopy.exe $source $install /E /XD '.venv' '__pycache__' 'dist' 'build' /XF '*.pyc' | Out-Null
if ($LASTEXITCODE -ge 8) { throw "Falha ao copiar os arquivos (robocopy $LASTEXITCODE)." }

$venv = Join-Path $install '.venv'
$venvPython = Join-Path $venv 'Scripts\python.exe'
if (-not (Test-Path -LiteralPath $venvPython)) {
    & $PythonExe -m venv $venv
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao criar o ambiente virtual.' }
}

$wheelhouse = Join-Path $install 'wheelhouse-win-amd64-py314'
if (Test-Path -LiteralPath $wheelhouse) {
    & $venvPython -m pip install --no-index --find-links $wheelhouse -r (Join-Path $install 'requirements.txt')
} else {
    & $venvPython -m pip install -r (Join-Path $install 'requirements.txt')
}
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias.' }

$uninstaller = @'
$ErrorActionPreference = 'Stop'
$root = Join-Path $env:ProgramFiles 'FluxoLoad'
Remove-Item -LiteralPath 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\FluxoLoad' -Recurse -Force -ErrorAction SilentlyContinue
$desktop = [Environment]::GetFolderPath('Desktop')
Remove-Item -LiteralPath (Join-Path $desktop 'FluxoLoad.lnk') -Force -ErrorAction SilentlyContinue
$startMenu = Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\FluxoLoad'
Remove-Item -LiteralPath $startMenu -Recurse -Force -ErrorAction SilentlyContinue
$cmd = Join-Path $env:TEMP ('FluxoLoad-remove-' + [guid]::NewGuid().ToString('N') + '.cmd')
$content = "@echo off`r`ntimeout /t 2 /nobreak >nul`r`nrmdir /s /q `"$root`"`r`ndel /q `"%~f0`""
Set-Content -LiteralPath $cmd -Encoding ASCII -Value $content
Start-Process -FilePath $env:ComSpec -ArgumentList "/c `"$cmd`"" -WindowStyle Hidden
'@
Set-Content -LiteralPath (Join-Path $install 'uninstall_fluxoload.ps1') -Value $uninstaller -Encoding UTF8

$uninstallCmd = Join-Path $install 'desinstalar_fluxoload.cmd'
$uninstallBatch = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -Command `"Start-Process powershell.exe -Verb RunAs -Wait -ArgumentList ('-NoProfile -ExecutionPolicy Bypass -File `"`"%ProgramFiles%\\FluxoLoad\\uninstall_fluxoload.ps1`"`"')`"`r`n"
Set-Content -LiteralPath $uninstallCmd -Value $uninstallBatch -Encoding ASCII

New-Item -Path $uninstallKey -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name DisplayName -Value 'FluxoLoad' -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name DisplayVersion -Value '1.2.0' -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name Publisher -Value 'FluxoLoad' -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name InstallLocation -Value $install -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name UninstallString -Value ('"' + $uninstallCmd + '"') -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name QuietUninstallString -Value ('"' + $uninstallCmd + '"') -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name DisplayIcon -Value (Join-Path $install 'assets\fluxoload-icon.ico') -PropertyType String -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name NoModify -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $uninstallKey -Name NoRepair -Value 1 -PropertyType DWord -Force | Out-Null

$desktop = [Environment]::GetFolderPath('Desktop')
$startMenu = Join-Path $env:ProgramData 'Microsoft\Windows\Start Menu\Programs\FluxoLoad'
New-Item -ItemType Directory -Path $startMenu -Force | Out-Null
$shell = New-Object -ComObject WScript.Shell
$pythonw = Join-Path $venv 'Scripts\pythonw.exe'
if (-not (Test-Path -LiteralPath $pythonw)) { $pythonw = $venvPython }
$icon = Join-Path $install 'assets\fluxoload-icon.ico'
foreach ($linkPath in @((Join-Path $desktop 'FluxoLoad.lnk'), (Join-Path $startMenu 'FluxoLoad.lnk'))) {
    $link = $shell.CreateShortcut($linkPath)
    $link.TargetPath = $pythonw
    $link.Arguments = '"' + (Join-Path $install 'run.py') + '"'
    $link.WorkingDirectory = $install
    if (Test-Path -LiteralPath $icon) { $link.IconLocation = $icon + ',0' }
    $link.Description = 'Iniciar FluxoLoad'
    $link.Save()
}

Start-Process -FilePath $pythonw -ArgumentList ('"' + (Join-Path $install 'run.py') + '"') -WorkingDirectory $install
Stop-Transcript | Out-Null
