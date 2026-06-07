# GULP
Accessing NEX-GDDP downscaled and bias-corrected climate projections often involves navigating dozens of GCMs and thousands of files. GULP (GDDP Unified Loader and Processor) simplifies the process with a one-click workflow, helping researchers save time on data acquisition and focus on generating scientific insights.

# DEVELOPMENT UNDER PROGRESS

# GULP — GDDP Unified Loader and Processor

![GULP Logo](GULP/assets/gulp.png)

> A dark, modern GUI tool for browsing and bulk-downloading
> NASA NEX-GDDP-CMIP6 climate datasets from the public AWS S3 bucket.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Output Structure](#output-structure)
7. [Build Instructions](#build-instructions)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The **NASA NEX-GDDP-CMIP6** dataset provides statistically downscaled daily
climate projections from 35+ CMIP6 models across multiple SSP scenarios at
0.25° spatial resolution. GULP gives you a clean GUI to browse, filter, and
download any subset of these datasets in parallel.

---

## Features

| Feature | Detail |
|---|---|
| **Modern dark GUI** | PyQt6 — three-step sidebar workflow |
| **Model browser** | Lists all available CMIP6 models from S3 |
| **Live scan log** | Real-time activity log while scanning |
| **Filter panel** | Checkboxes for scenario / variable / version |
| **Combination table** | Sortable, color-coded results table |
| **Parallel downloads** | Configurable worker count (default 16) |
| **Resume support** | Already-downloaded files are skipped |
| **Progress bar** | Per-file download progress with percentage |
| **Output folder picker** | Choose any local destination folder |

---

## Requirements

| Requirement | Version |
|---|---|
| Python | ≥ 3.9 |
| PyQt6 | ≥ 6.6.0 |
| requests | ≥ 2.31.0 |

---

## Installation

### Windows (Installer)

1. Download `GULP_Setup_1.0.0.exe` from the Releases page.
2. Run the installer — it installs PyQt6 and requests automatically.
3. Launch **GULP** from the Start Menu or Desktop shortcut.

> **Note:** Python 3.9+ must be installed and on `PATH` first.  
> Get it at https://www.python.org/downloads/ — check *Add Python to PATH*.

### Windows (Manual)

```bat
git clone https://github.com/your-org/gulp.git
cd gulp
pip install -r requirements.txt
gulp.bat
```

### Linux / macOS

```bash
git clone https://github.com/your-org/gulp.git
cd gulp
chmod +x gulp.sh
./gulp.sh
```

On Linux, if Qt complains about missing platform plugins:
```bash
sudo apt install libxcb-cursor0   # Ubuntu/Debian
```

---

## Usage

GULP has a three-step sidebar workflow:

### Step 1 — Models

- GULP loads all available CMIP6 models from the S3 bucket.
- Select one or more models (Ctrl+Click or Shift+Click for multi-select).
- Click **Scan Selected →**.

### Step 2 — Scan

- GULP scans the S3 bucket for every scenario / realization / variable / version
  combination available for your chosen models.
- A live activity log shows progress.

### Step 3 — Download

- Use the **filter checkboxes** (Scenario, Variable, Version) to narrow down
  combinations. The table updates instantly.
- Click **Resolve Files** to count the exact `.nc` files that match.
- Choose an **output folder** and set the number of **workers**.
- Click **⬇ Download** to start. A progress bar and live log track each file.

---

## Output Structure

```
NEX_GDDP/
└── ACCESS-CM2/
    └── historical/
        └── pr/
            ├── pr_day_ACCESS-CM2_historical_r1i1p1f1_gn_1950.nc
            ├── pr_day_ACCESS-CM2_historical_r1i1p1f1_gn_1951.nc
            └── ...
```

---

## Build Instructions

See [BUILD.md](BUILD.md) for full instructions on producing:

- A standalone `GULP.exe` via PyInstaller (no Python needed on target machine)
- A Windows installer `GULP_Setup_1.0.0.exe` via Inno Setup 6

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Python was not found` | Install Python 3.9+ and add to PATH |
| `No module named PyQt6` | Run `pip install PyQt6` |
| `Could not load Qt platform plugin` | On Linux: `sudo apt install libxcb-cursor0` |
| Model list empty | Check your network / firewall — S3 must be reachable |
| Slow downloads | Increase Workers in the Download panel |
| Corrupt `.nc` files | Delete partial file and re-run — GULP will re-download |

---

*GULP is an independent project and is not affiliated with NASA or Amazon Web Services.*
