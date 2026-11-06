
#define MyAppName "LaPauta Capture Studio"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "LaPauta Audio"

[Setup]
AppId={{8D2A5B21-77F4-4A12-9D10-583104290001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\LaPauta Capture Studio
DefaultGroupName=LaPauta Capture Studio
OutputDir=installer
OutputBaseFilename=LaPautaCaptureStudio-Setup
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
WizardStyle=modern
UninstallDisplayIcon={app}\LaPautaCaptureStudio.exe

[Files]
Source: "dist\LaPautaCaptureStudio.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\LaPauta Capture Studio"; Filename: "{app}\LaPautaCaptureStudio.exe"
Name: "{autodesktop}\LaPauta Capture Studio"; Filename: "{app}\LaPautaCaptureStudio.exe"

[Run]
Filename: "{app}\LaPautaCaptureStudio.exe"; Description: "Abrir LaPauta Capture Studio"; Flags: postinstall nowait skipifsilent
