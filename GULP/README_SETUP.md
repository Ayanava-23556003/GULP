# GULP — Setup & Launch

These launcher scripts let you (or anyone you hand this folder to) run GULP
on a computer that may not have Python installed at all yet — no manual
setup required.

## Usage

| Platform | Run this |
|---|---|
| Windows  | double-click `run_gulp_windows.bat` |
| macOS    | double-click `run_gulp_macos.command` (first time: right-click → Open, to bypass Gatekeeper) |
| Linux    | `./run_gulp_linux.sh` in a terminal |

Each script:
1. Checks if Python is already installed.
2. **If not**, downloads and installs it automatically:
   - Windows → official python.org installer, per-user (no admin needed), added to PATH.
   - macOS → via Homebrew (installs Homebrew first if missing).
   - Linux → via your distro's package manager (`apt`/`dnf`/`yum`/`pacman`/`zypper`), needs `sudo`.
3. Launches `gulp_gui.py`, which **auto-installs any missing Python packages**
   (`requests`, `PyQt6`, and — for the shapefile-clipping feature —
   `geopandas`, `xarray`, `rioxarray`) the first time it runs.

To launch the command-line version instead of the GUI, edit the last line
of the relevant launcher script, replacing `gulp_gui.py` with `gulp.py`.

## Things to know

- **Internet connection is required** the first time, to download Python
  and/or the pip packages.
- **Windows:** the installer runs per-user (no admin password needed). If a
  brand-new PATH entry doesn't show up in *other* already-open terminals,
  that's normal — it's picked up by new windows/sessions automatically.
- **Linux:** installing Python system-wide needs `sudo`; you'll be prompted
  for your password.
- **macOS:** if Homebrew isn't installed, the script installs it first,
  which can take a few minutes.
- If automatic installation fails for any reason (restricted network,
  unsupported OS version, no admin/sudo rights, etc.), each script prints
  a clear error and a link to install Python manually — after that,
  everything else still works the same way.
- The shapefile-clipping packages (`geopandas`/`xarray`/`rioxarray`) are
  the heaviest install. If they fail to install (e.g. fully offline
  machine), GULP still runs fine — the "Clip to shapefile" option in the
  download popup is just disabled, and full files download as normal.

## Files

- `gulp_gui.py` — the GUI application
- `gulp.py` — the command-line version
- `run_gulp_windows.bat` / `run_gulp_macos.command` / `run_gulp_linux.sh` — setup + launch scripts
