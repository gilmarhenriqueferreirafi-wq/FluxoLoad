#define MyAppName "FluxoLoad"
#define MyAppVersion "1.1.0"
#define MyAppPublisher "FluxoLoad"
#define MyAppExeName "FluxoLoad.exe"

[Setup]
AppId={{A7B5A4D4-3F9C-4F8A-9F8C-110011001100}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL=https://github.com/gilmarhenriqueferreirafi-wq/FluxoLoad
DefaultDirName={autopf}\FluxoLoad
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=no
LicenseFile=TERMOS-DE-USO.txt
SetupIconFile=assets\fluxoload-icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
OutputDir=installer\output
OutputBaseFilename=FluxoLoad-1.1.0-Setup-v2
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion=1.1.0.0
VersionInfoProductName=FluxoLoad
VersionInfoDescription=Downloader autorizado com navegador interno

[Languages]
Name: "brazilianportuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"; Flags: unchecked

[Files]
Source: "dist\FluxoLoad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "AVISO-SMARTSCREEN.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "executar_fluxoload.cmd"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon

[UninstallDelete]
; Os dados do usuário, perfil do navegador e downloads não são removidos.
