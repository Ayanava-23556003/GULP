#!/bin/bash
# GULP - GDDP Unified Loader & Processor
# Setup & Launch (macOS)
set -e
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "  GULP - GDDP Unified Loader and Processor"
echo "  Setup & Launch (macOS)"
echo "============================================================"
echo

PYEXE=""
if command -v python3 >/dev/null 2>&1; then
    PYEXE="python3"
fi

if [ -z "$PYEXE" ]; then
    echo "Python 3 was not found on this Mac. Installing it now..."
    echo

    if ! command -v brew >/dev/null 2>&1; then
        echo "Homebrew (package manager) not found — installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        # Make brew available in this session (Apple Silicon vs Intel paths)
        if [ -x /opt/homebrew/bin/brew ]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [ -x /usr/local/bin/brew ]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
    fi

    echo "Installing Python via Homebrew..."
    brew install python

    if command -v python3 >/dev/null 2>&1; then
        PYEXE="python3"
    else
        echo "[ERROR] Python installation did not complete as expected."
        echo "Please install Python manually from https://www.python.org/downloads/"
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
