; Inno Setup script for VideoTranscriber
#define MyAppName "VideoTranscriber"
#define MyAppVersion GetEnv("APP_VERSION") != "" ? GetEnv("APP_VERSION") : "0.0.0"
#define MyAppPublisher "VideoTranscriber"
#define MyAppExeName "VideoTranscriber.exe"
#define MySourceDir "..\dist\VideoTranscriber"

[Setup]
AppId={{C95B0C75-6F41-4C27-8455-8EE2D6437F29}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputBaseFilename={#MyAppName}-Setup-{#MyAppVersion}
OutputDir=..\dist
DisableDirPage=no
DisableProgramGroupPage=no
Compression=lzma
SolidCompression=yes
SetupIconFile=..\assets\app.ico
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop icon"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "{#MySourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch {#MyAppName}"; Flags: nowait postinstall skipifsilent
