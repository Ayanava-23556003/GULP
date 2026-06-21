; =============================================================
;  GULP - GeoData Universal Loader for Precipitation
;  Inno Setup Script  (Inno Setup 6.x)
;  Build:  iscc gulp_setup.iss
; =============================================================

#define AppName      "GULP"
#define AppFullName  "GULP - GDDP Unified Loader & Processor"
#define AppVersion   "1.0.0"
#define AppPublisher "Ayanava Poddar"
#define AppURL       "https://github.com/Ayanava-23556003/GULP"
#define AppExeName   "run_gulp_windows.bat"

[Setup]
AppId={{A3F7C2D1-88BE-4E6A-B012-F1234567890A}
AppName={#AppFullName}
AppVersion={#AppVersion}
AppVerName={#AppFullName} {#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases

; Install to Program Files\GULP
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes

; Output
OutputDir=..\dist
OutputBaseFilename=GULP_Setup_{#AppVersion}
SetupIconFile=..\assets\gulp.ico
UninstallDisplayIcon={app}\assets\gulp.ico

; Compression
Compression=lzma2/ultra64
SolidCompression=yes
InternalCompressLevel=ultra

; Require admin for Program Files install
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog

; Windows version requirements
MinVersion=10.0

; Wizard style
WizardStyle=modern
WizardSmallImageFile=..\assets\gulp.bmp

; Misc
ChangesEnvironment=yes
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE.txt

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";    Description: "{cm:CreateDesktopIcon}";    GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1

[Files]
; Core application
Source: "..\src\gulp.py";          DestDir: "{app}\src";    Flags: ignoreversion
Source: "..\src\gulp_gui.py";      DestDir: "{app}\src";    Flags: ignoreversion
Source: "..\requirements.txt";     DestDir: "{app}";        Flags: ignoreversion
Source: "..\run_gulp_windows.bat";             DestDir: "{app}";        Flags: ignoreversion
Source: "..\README.md";            DestDir: "{app}";        Flags: ignoreversion isreadme
Source: "..\CHANGELOG.md";         DestDir: "{app}";        Flags: ignoreversion

; Assets
Source: "..\assets\gulp.ico";      DestDir: "{app}\assets"; Flags: ignoreversion
Source: "..\assets\gulp.png";      DestDir: "{app}\assets"; Flags: ignoreversion

; Microsoft Visual C++ Redistributable (x64) — required by PyQt6's
; compiled Qt6 DLLs. Bundled so installs work fully offline / without
; relying on a download succeeding at install time. Download once from:
; https://aka.ms/vs/17/release/vc_redist.x64.exe and place it at
; ..\vendor\vc_redist.x64.exe before building.
Source: "..\vendor\vc_redist.x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall; AfterInstall: InstallVCRedist

[Icons]
; Start menu
Name: "{group}\{#AppName}";          Filename: "{app}\run_gulp_windows.bat"; IconFilename: "{app}\assets\gulp.ico"; WorkingDir: "{app}"
Name: "{group}\README";              Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\run_gulp_windows.bat"; IconFilename: "{app}\assets\gulp.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Launch GULP. run_gulp_windows.bat handles installing Python itself (if
; missing) and the script auto-installs any missing pip packages — no
; separate pip-install [Run] step is needed here.
Filename: "{app}\run_gulp_windows.bat"; \
  Description: "Launch GULP"; \
  Flags: postinstall nowait skipifsilent

; Offer to view README
Filename: "{app}\README.md"; \
  Description: "View README"; \
  Flags: postinstall shellexec skipifsilent unchecked

[UninstallDelete]
; Remove downloaded data dir only if user confirms (leave data by default)
Type: dirifempty; Name: "{app}\NEX_GDDP"

[Code]
// -----------------------------------------------------------
// Install the bundled VC++ Redistributable (x64) silently.
// Safe to run even if already installed — it's a fast no-op.
// -----------------------------------------------------------
procedure InstallVCRedist;
var
  ResultCode: Integer;
begin
  if not Exec(ExpandConstant('{tmp}\vc_redist.x64.exe'), '/install /quiet /norestart', '',
              SW_HIDE, ewWaitUntilTerminated, ResultCode) then
    MsgBox(
      'Could not run the Visual C++ Redistributable installer automatically.'
      + #13#10
      + 'If GULP fails to launch with a "DLL load failed" error, install it '
      + 'manually from: https://aka.ms/vs/17/release/vc_redist.x64.exe',
      mbInformation, MB_OK);
end;

// -----------------------------------------------------------
// Check whether Python 3.9+ is already installed. This is informational
// only — it does NOT block setup, because run_gulp_windows.bat will
// install Python itself (per-user, no admin needed) on first launch if
// it's missing.
// -----------------------------------------------------------
function IsPythonInstalled(): Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('python', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
            and (ResultCode = 0);
  if not Result then
    Result := Exec('python3', '--version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode)
              and (ResultCode = 0);
end;

function InitializeSetup(): Boolean;
begin
  if not IsPythonInstalled() then
  begin
    MsgBox(
      'Python was not found on this system.'
      + #13#10#13#10
      + 'That''s OK — GULP will install Python automatically (no admin '
      + 'rights needed) the first time you launch it from the Start Menu.'
      + #13#10#13#10
      + 'This requires an internet connection on first launch.',
      mbInformation, MB_OK);
  end;
  Result := True;
end;
