#ifndef AppVersion
  #define AppVersion "0.1.0"
#endif
[Setup]
AppId={{C5F4B5BF-E205-4E34-8878-A328CA9E05EB}
AppName=Video Transcriber
AppVersion={#AppVersion}
DefaultDirName={localappdata}\Programs\Video Transcriber
DefaultGroupName=Video Transcriber
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
OutputDir=..\release
OutputBaseFilename=Video-Transcriber-Windows-x64-Setup
SetupIconFile=..\build\icon.ico
UninstallDisplayIcon={app}\Video Transcriber.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
[Files]
Source: "..\dist\Video Transcriber\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
[Icons]
Name: "{group}\Video Transcriber"; Filename: "{app}\Video Transcriber.exe"
Name: "{autodesktop}\Video Transcriber"; Filename: "{app}\Video Transcriber.exe"; Tasks: desktopicon
[Tasks]
Name: desktopicon; Description: "Create a desktop shortcut"; Flags: unchecked
[Run]
Filename: "{app}\Video Transcriber.exe"; Description: "Launch Video Transcriber"; Flags: nowait postinstall skipifsilent
