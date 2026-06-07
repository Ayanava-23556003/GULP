#!/usr/bin/env bash
# GULP — GUI launcher for Linux/macOS

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON=""
for cmd in python3 python; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        MAJ="${VER%%.*}"; MIN="${VER##*.}"
        if [[ "$MAJ" -ge 3 && "$MIN" -ge 9 ]]; then
            PYTHON="$cmd"; break
        fi
    fi
done

if [[ -z "$PYTHON" ]]; then
    echo "[ERROR] Python 3.9+ not found."
    exit 1
fi

echo "Installing / checking dependencies..."
"$PYTHON" -m pip install -r "$SCRIPT_DIR/requirements.txt" \
    --quiet --disable-pip-version-check || true

"$PYTHON" "$SCRIPT_DIR/src/gulp_gui.py" "$@"
