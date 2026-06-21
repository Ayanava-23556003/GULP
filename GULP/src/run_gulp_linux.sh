#!/bin/bash
# GULP - GDDP Unified Loader & Processor
# Setup & Launch (Linux)
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  GULP - GDDP Unified Loader and Processor"
echo "  Setup & Launch (Linux)"
echo "============================================================"
echo

PYEXE=""
if command -v python3 >/dev/null 2>&1; then
    PYEXE="python3"
fi

if [ -z "$PYEXE" ]; then
    echo "Python 3 was not found. Installing it now (this requires sudo)..."
    echo

    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y python3 python3-pip
    elif command -v yum >/dev/null 2>&1; then
        sudo yum install -y python3 python3-pip
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -Sy --noconfirm python python-pip
    elif command -v zypper >/dev/null 2>&1; then
        sudo zypper install -y python3 python3-pip
    else
        echo "[ERROR] Could not detect a supported package manager"
        echo "(apt, dnf, yum, pacman, zypper)."
        echo "Please install Python 3 manually for your distribution."
        exit 1
    fi

    if command -v python3 >/dev/null 2>&1; then
        PYEXE="python3"
    else
        echo "[ERROR] Python installation did not complete as expected."
        exit 1
    fi
    echo
fi

echo "Using Python:"
"$PYEXE" --version
echo

# GULP itself auto-installs any missing pip packages on startup.
echo "Launching GULP GUI ..."
echo
"$PYEXE" "$DIR/gulp_gui.py"
