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

[Icons]
; Start menu
Name: "{group}\{#AppName}";          Filename: "{app}\run_gulp_windows.bat"; IconFilename: "{app}\assets\gulp.ico"; WorkingDir: "{app}"
Name: "{group}\README";              Filename: "{app}\README.md"
Name: "{group}\{cm:UninstallProgram,{#AppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#AppName}";    Filename: "{app}\run_gulp_windows.bat"; IconFilename: "{app}\assets\gulp.ico"; WorkingDir: "{app}"; Tasks: desktopicon

[Run]
; Install Python dependencies (requests, PyQt6) after setup
Filename: "cmd.exe"; \
  Parameters: "/c python -m pip install -r ""{app}\requirements.txt"" --quiet"; \
  Description: "Install Python dependencies (PyQt6, requests)"; \
  Flags: runhidden waituntilterminated; \
  StatusMsg: "Installing Python dependencies (PyQt6, requests)..."

; Launch GULP
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
// Check that Python 3.9+ is installed before proceeding
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
      'Python 3.9 or later is required by GULP but was not found on this system.'
      + #13#10#13#10
      + 'Please install Python from https://www.python.org/downloads/'
      + #13#10
      + 'and make sure "Add Python to PATH" is checked during installation.'
      + #13#10#13#10
      + 'Setup will now exit.',
      mbError, MB_OK);
    Result := False;
  end else
    Result := True;
end;
