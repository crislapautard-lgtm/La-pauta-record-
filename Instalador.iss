
[Setup]
AppId={{A73D8D12-5C19-4D89-9B25-6D5F8B6A1001}
AppName=La Pauta Capture
AppVersion=1.0.0
AppPublisher=La Pauta
DefaultDirName={autopf}\La Pauta Capture
DefaultGroupName=La Pauta Capture
OutputDir=installer_output
OutputBaseFilename=LaPautaCaptureSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin

[Files]
Source: "dist\LaPautaCapture.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"
Name: "{commondesktop}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"
