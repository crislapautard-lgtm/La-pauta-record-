
#define MyAppName "La Pauta Capture"
#define MyAppVersion "1.0.1"
#define MyAppPublisher "LaPauta Audio"

[Setup]
AppId={{58310429-1073-4072-9080-583104290001}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\LaPauta Capture
DefaultGroupName=LaPauta Capture
OutputDir=installer
OutputBaseFilename=LaPautaCaptureSetup
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Files]
Source: "dist\LaPautaCapture.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\LaPauta Capture"; Filename: "{app}\LaPautaCapture.exe"
Name: "{autodesktop}\LaPauta Capture"; Filename: "{app}\LaPautaCapture.exe"

[Run]
Filename: "{app}\LaPautaCapture.exe"; Description: "Abrir LaPauta Capture"; Flags: postinstall nowait skipifsilent
