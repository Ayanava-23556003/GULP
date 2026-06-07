@echo off
setlocal

REM ── Set GULP_DIR to the folder containing this .bat ──────────────────────
set "GULP_DIR=%~dp0"
REM %~dp0 always ends with \, e.g. C:\Tools\GULP\
REM So paths like %GULP_DIR%src\gulp_gui.py are always correct.

REM ── Locate python.exe ─────────────────────────────────────────────────────
set "PYTHON="
python --version >nul 2>&1
if %errorlevel% EQU 0 set "PYTHON=python"

if "%PYTHON%"=="" (
    echo [ERROR] Python not found in PATH.
    echo Install Python 3.9+ from https://www.python.org/downloads/
    echo Make sure "Add Python to PATH" is ticked during install.
    pause
    exit /b 1
)

REM ── Install / update dependencies silently ───────────────────────────────
%PYTHON% -m pip install -r "%GULP_DIR%requirements.txt" --quiet --disable-pip-version-check

REM ── Find pythonw.exe (same folder as python.exe, always on Windows) ───────
for /f "delims=" %%I in ('where python') do set "PYTHON_EXE=%%I" & goto :found_python
:found_python

REM pythonw lives beside python in the same Scripts / base folder
set "PYTHONW_EXE=%PYTHON_EXE:python.exe=pythonw.exe%"

if not exist "%PYTHONW_EXE%" (
    REM Fallback: try PATH
    where pythonw >nul 2>&1
    if %errorlevel% EQU 0 (
        set "PYTHONW_EXE=pythonw"
    ) else (
        REM Last resort: run with python (terminal briefly flashes then closes)
        set "PYTHONW_EXE=%PYTHON_EXE%"
    )
)

REM ── Launch GUI — no console window ────────────────────────────────────────
REM   start "" /b  =  launch detached, no new window, bat exits immediately
start "" /b "%PYTHONW_EXE%" "%GULP_DIR%src\gulp_gui.py"

endlocal
