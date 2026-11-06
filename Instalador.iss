[Setup]
AppName=La Pauta Capture
AppVersion=1.0
AppPublisher=La Pauta
DefaultDirName={pf}\La Pauta Capture
DefaultGroupName=La Pauta Capture
OutputDir=dist
OutputBaseFilename=LaPautaCaptureSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\LaPautaCapture.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"
Name: "{commondesktop}\La Pauta Capture"; Filename: "{app}\LaPautaCapture.exe"
