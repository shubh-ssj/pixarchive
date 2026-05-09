; ─────────────────────────────────────────────────────────────────────────────
;  PixArchive — Inno Setup 6 installer script
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "PixArchive"
#define AppVersion   "1.6.0"
#define AppPublisher "SSJ"
#define AppURL       "https://github.com/shubh-ssj/pixarchive"
#define AppExeName   "pixarchive.exe"
#define SourceDir    "..\dist\pixarchive"
#define OutputDir    "."

#define WizardSidebar  "..\assets\banner_sidebar.bmp"
#define WizardHeader   "..\assets\banner_header.bmp"

[Setup]
AppId={{8A3F2C1D-4B9E-4F7A-B6C2-1D3E5F8A9B0C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

DefaultDirName={autopf}\PixArchive
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=pixarchive-setup
SetupIconFile=..\assets\icon.ico

Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

MinVersion=10.0

WizardStyle=modern
WizardSizePercent=110
ShowLanguageDialog=no
WizardImageFile={#WizardSidebar}
WizardSmallImageFile={#WizardHeader}

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Create a &desktop shortcut";     GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";  Description: "Launch at &Windows startup";      GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "addtopath";    Description: "Add install directory to &PATH";  GroupDescription: "System integration:";   Flags: unchecked

[Files]
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#AppName}";           Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";     Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Registry]
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{olddata};{app}"; Tasks: addtopath; Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[Code]

function NeedsAddPath(Param: string): boolean;
var
  OrigPath: string;
begin
  if not RegQueryStringValue(HKCU, 'Environment', 'Path', OrigPath) then
  begin
    Result := True;
    exit;
  end;
  Result := Pos(';' + Uppercase(Param) + ';', ';' + Uppercase(OrigPath) + ';') = 0;
end;

procedure InitializeWizard();
var
  WelcomeText: string;
  FinishText: string;
begin
  // KEY FIX: #13#10 is always at the END of a line, never the start.
  // Leading '#' on any line is parsed by ISPP as a directive — causing the
  // "Unknown preprocessor directive" error seen in the screenshot.
  WelcomeText :=
    'This will install PixArchive {#AppVersion} on your computer.' + #13#10 + #13#10 +
    'PixArchive is an image downloader utility that lets you ' +
    'archive image galleries and collections from 200+ websites.' + #13#10 + #13#10 +
    'Note: gallery-dl is not bundled. The app will offer to install it ' +
    'via pip on first launch if it is not already present.' + #13#10 + #13#10 +
    'Click Next to continue.';

  FinishText :=
    'PixArchive {#AppVersion} has been successfully installed.' + #13#10 + #13#10 +
    'Click Finish to close Setup.';

  WizardForm.WelcomeLabel2.Caption := WelcomeText;
  WizardForm.FinishedLabel.Caption := FinishText;
  WizardForm.WizardBitmapImage.Stretch  := True;
  WizardForm.WizardBitmapImage2.Stretch := True;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // Add post-install steps here if needed.
  end;
end;
