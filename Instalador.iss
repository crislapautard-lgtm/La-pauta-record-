
[Setup]
AppId={{A73D8D12-5C19-4D89-9B25-6D5F8B6A1001}
AppName=La Pauta Capture
AppVersion=1.0.1
AppPublisher=La Pauta
DefaultDirName={autopf}\La Pauta Capture
DefaultGroupName=La Pauta Capture
OutputDir=dist
OutputBaseFilename=LaPautaCaptureSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
UninstallDisplayIcon={app}\LaPautaCapture.exe
DisableProgramGroupPage=yes

[Files]
Source: "dist\LaPautaCapture.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"
Name: "{commondesktop}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"
