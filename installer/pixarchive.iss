; ─────────────────────────────────────────────────────────────────────────────
;  PixArchive — Inno Setup 6 installer script
;
;  Prerequisites:
;    1. Run build.bat first to produce dist\pixarchive\
;    2. Install Inno Setup 6: https://jrsoftware.org/isdl.php
;    3. Compile this script with ISCC.exe, or open in Inno Setup IDE
;
;  Output: installer\pixarchive-setup.exe
; ─────────────────────────────────────────────────────────────────────────────

#define AppName      "PixArchive"
#define AppVersion   "1.6.0"
#define AppPublisher "SSJ"
#define AppURL       "https://github.com/shubh-ssj/pixarchive"
#define AppExeName   "pixarchive.exe"
#define SourceDir    "..\dist\pixarchive"
#define OutputDir    "."

[Setup]
; Basic identity
AppId={{8A3F2C1D-4B9E-4F7A-B6C2-1D3E5F8A9B0C}
AppName={#AppName}
AppVersion={#AppVersion}
AppVerName={#AppName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}
AppUpdatesURL={#AppURL}

; Install location
DefaultDirName={autopf}\PixArchive
DefaultGroupName={#AppName}
DisableProgramGroupPage=yes
OutputDir={#OutputDir}
OutputBaseFilename=pixarchive-setup
SetupIconFile=..\assets\icon.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes

; Windows version requirement
MinVersion=10.0

; Appearance
WizardStyle=modern
WizardSizePercent=110
ShowLanguageDialog=no

; Privileges — install per-user by default (no UAC prompt needed)
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Uninstaller
UninstallDisplayName={#AppName}
UninstallDisplayIcon={app}\{#AppExeName}

; Restart
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "Create a &desktop shortcut";          GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "startupicon";    Description: "Launch at &Windows startup";           GroupDescription: "Additional shortcuts:"; Flags: unchecked
Name: "addtopath";      Description: "Add install directory to &PATH";       GroupDescription: "System integration:";   Flags: unchecked

[Files]
; Copy everything from the PyInstaller output folder
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start menu
Name: "{group}\{#AppName}";            Filename: "{app}\{#AppExeName}"
Name: "{group}\Uninstall {#AppName}";  Filename: "{uninstallexe}"

; Desktop (optional task)
Name: "{autodesktop}\{#AppName}";      Filename: "{app}\{#AppExeName}"; Tasks: desktopicon

; Startup (optional task)
Name: "{userstartup}\{#AppName}";      Filename: "{app}\{#AppExeName}"; Tasks: startupicon

[Registry]
; File type association — open .txt files containing URL lists with the app
; (commented out — uncomment if you want this)
; Root: HKCU; Subkey: "Software\Classes\.gdllist"; ValueType: string; ValueName: ""; ValueData: "GalleryDLList"; Flags: uninsdeletevalue
; Root: HKCU; Subkey: "Software\Classes\GalleryDLList\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#AppExeName}"" ""%1"""; Flags: uninsdeletekey

; Add to PATH (optional task)
Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path";
    ValueData: "{olddata};{app}"; Tasks: addtopath;
    Check: NeedsAddPath(ExpandConstant('{app}'))

[Run]
; Offer to launch the app after install
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Kill the process before uninstalling
Filename: "taskkill.exe"; Parameters: "/f /im {#AppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[Code]
// ── NeedsAddPath: only add to PATH if not already there ─────────────────────
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

// ── Welcome page custom text ─────────────────────────────────────────────────
function GetWelcomeLabel(Default: string): string;
begin
  Result :=
    'This will install PixArchive ' + '{#AppVersion}' + ' on your computer.' + #13#10 +
    #13#10 +
    'PixArchive is an image downloader utility that lets you ' +
    'archive image galleries and collections from 200+ websites.' + #13#10 +
    #13#10 +
    'Note: gallery-dl itself is not bundled. The app will offer to install it ' +
    'via pip on first launch if it is not already present.' + #13#10 +
    #13#10 +
    'Click Next to continue.';
end;
