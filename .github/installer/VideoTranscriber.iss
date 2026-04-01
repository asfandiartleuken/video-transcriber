; Inno Setup script for VideoTranscriber
#define MyAppName "VideoTranscriber"
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0"
#endif
#define MyAppPublisher "asfandiartleuken"
#define MyAppExeName "VideoTranscriber.exe"

[Setup]
AppId={{9C9D8A67-3C4D-4E2A-B677-7F0F0301D7C6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=VideoTranscriber-Setup
OutputDir=..\..
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ChangesEnvironment=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "addtoolstopath"; Description: "Add bundled ffmpeg / yt-dlp tools to PATH"; GroupDescription: "Environment:"

[Files]
Source: "..\..\dist\VideoTranscriber\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
const
  EnvironmentKey = 'Environment';
  PathValueName = 'Path';

function AddPathEntry(CurrentPath, Entry: string): string;
begin
  if (CurrentPath = '') then
    Result := Entry
  else if Pos(';' + Uppercase(Entry) + ';', ';' + Uppercase(CurrentPath) + ';') > 0 then
    Result := CurrentPath
  else
    Result := CurrentPath + ';' + Entry;
end;

function RemovePathEntry(CurrentPath, Entry: string): string;
var
  Parts: TArrayOfString;
  I: Integer;
  Filtered: string;
begin
  Filtered := '';
  Parts := SplitString(CurrentPath, ';');
  for I := 0 to GetArrayLength(Parts) - 1 do begin
    if CompareText(Trim(Parts[I]), Entry) <> 0 then begin
      if Filtered <> '' then
        Filtered := Filtered + ';';
      Filtered := Filtered + Parts[I];
    end;
  end;
  Result := Filtered;
end;

procedure UpdateUserPath(AddEntry: Boolean);
var
  CurrentPath: string;
  ToolsPath: string;
  NewPath: string;
begin
  ToolsPath := ExpandConstant('{app}\tools');
  if not RegQueryStringValue(HKCU, EnvironmentKey, PathValueName, CurrentPath) then
    CurrentPath := '';

  if AddEntry then
    NewPath := AddPathEntry(CurrentPath, ToolsPath)
  else
    NewPath := RemovePathEntry(CurrentPath, ToolsPath);

  if NewPath = '' then
    RegDeleteValue(HKCU, EnvironmentKey, PathValueName)
  else
    RegWriteExpandStringValue(HKCU, EnvironmentKey, PathValueName, NewPath);

  Log(Format('Updated user PATH with tools dir: %s', [ToolsPath]));
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsTaskSelected('addtoolstopath') then
    UpdateUserPath(True);
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
    UpdateUserPath(False);
end;
