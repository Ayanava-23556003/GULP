@echo off
setlocal enabledelayedexpansion
title GULP Setup ^& Launcher
cd /d "%~dp0"

echo ============================================================
echo   GULP - GDDP Unified Loader and Processor
echo   Setup ^& Launch (Windows)
echo ============================================================
echo.

REM ---- 1. Find an existing Python ----
set "PYEXE="
where python >nul 2>nul
if %errorlevel%==0 (
    for /f "delims=" %%P in ('where python') do (
        if not defined PYEXE set "PYEXE=%%P"
    )
)
if not defined PYEXE (
    where py >nul 2>nul
    if !errorlevel!==0 set "PYEXE=py"
)

REM ---- 2. If not found, download + silently install Python (per-user, no admin) ----
if not defined PYEXE (
    echo Python was not found on this computer.
    echo Downloading and installing Python 3.12 ^(per-user, no admin rights needed^)...
    echo.

    set "PY_VER=3.12.4"
    set "PY_URL=https://www.python.org/ftp/python/!PY_VER!/python-!PY_VER!-amd64.exe"
    set "PY_INSTALLER=%TEMP%\gulp_python_installer.exe"

    powershell -NoProfile -Command "try { Invoke-WebRequest -Uri '!PY_URL!' -OutFile '!PY_INSTALLER!' -UseBasicParsing } catch { exit 1 }"
    if not exist "!PY_INSTALLER!" (
        echo [ERROR] Could not download the Python installer.
        echo Please install Python manually from https://www.python.org/downloads/
        echo and re-run this script.
        pause
        exit /b 1
    )

    echo Installing Python silently, this may take a minute...
    "!PY_INSTALLER!" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=1
    del "!PY_INSTALLER!" >nul 2>nul

    REM PrependPath updates the registry, but THIS already-running cmd
    REM session won't see it until restarted. Add the known per-user
    REM install location to PATH for the rest of this session manually.
    set "PYDIR=%LOCALAPPDATA%\Programs\Python\Python312"
    if exist "!PYDIR!\python.exe" (
        set "PATH=!PYDIR!;!PYDIR!\Scripts;!PATH!"
        set "PYEXE=!PYDIR!\python.exe"
        echo Python installed and added to PATH for this session.
        echo ^(It will also be available in new terminal windows from now on.^)
    ) else (
        echo [ERROR] Python installation did not complete as expected.
        echo Please install Python manually from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo.
)

echo Using Python:
"!PYEXE!" --version
echo.

REM ---- 3. Warn if running from a cloud-sync drive ----
REM Native DLLs (e.g. PyQt6's Qt6 DLLs) often fail to load correctly from
REM Google Drive / OneDrive / Dropbox sync folders even when the file
REM appears present. This doesn't block the run, just flags the likely
REM cause if something goes wrong below.
echo %~dp0 | findstr /I /C:"Google Drive" /C:"OneDrive" /C:"Dropbox" /C:"iCloudDrive" >nul
if !errorlevel!==0 (
    echo [WARNING] This folder is inside a cloud-sync drive:
    echo            %~dp0
    echo            Native DLLs ^(used by PyQt6^) can fail to load from here.
    echo            If you hit a "DLL load failed" error below, copy this
    echo            whole folder to a local path like C:\GULP and run it
    echo            from there instead.
    echo.
)

REM ---- 4. Ensure the Microsoft Visual C++ Redistributable (x64) is present ----
REM PyQt6's compiled Qt6 DLLs require this; a fresh Python install does
REM not include it, and a missing/outdated copy is the other common
REM cause of "DLL load failed while importing QtCore". Checking for the
REM actual DLL files in System32 is more reliable than the registry key,
REM which can report "installed" even when an older/partial copy is
REM present (vcruntime140_1.dll specifically was added in a later
REM update and is the one most often missing).
if not exist "%WINDIR%\System32\vcruntime140_1.dll" goto :install_vcredist
if not exist "%WINDIR%\System32\msvcp140.dll" goto :install_vcredist
goto :vcredist_done

:install_vcredist
echo Microsoft Visual C++ Redistributable ^(x64^) missing or out of date.
echo Downloading and installing it silently...
set "VC_INSTALLER=%TEMP%\gulp_vc_redist.x64.exe"
powershell -NoProfile -Command "try { Invoke-WebRequest -Uri 'https://aka.ms/vs/17/release/vc_redist.x64.exe' -OutFile '!VC_INSTALLER!' -UseBasicParsing } catch { exit 1 }"
if exist "!VC_INSTALLER!" (
    "!VC_INSTALLER!" /install /quiet /norestart
    del "!VC_INSTALLER!" >nul 2>nul
    echo Done.
) else (
    echo [WARNING] Could not download the VC++ Redistributable automatically.
    echo            If GULP fails with a "DLL load failed" error, install it
    echo            manually from: https://aka.ms/vs/17/release/vc_redist.x64.exe
)
echo.
:vcredist_done

REM ---- 5. Launch GULP. The script itself auto-installs any missing pip packages. ----
echo Launching GULP GUI ...
echo.
"!PYEXE!" "%~dp0gulp_gui.py"

echo.
pause