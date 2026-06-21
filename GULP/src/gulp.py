"""
GULP - GDDP Unified Loader & Processor
NASA NEX-GDDP-CMIP6 Dataset Downloader
Version 1.0.0
"""

import importlib.util
import os
import subprocess
import sys


# ─────────────────────────────────────────────
#  Auto-install missing dependencies
# ─────────────────────────────────────────────
# Runs before any third-party imports. Hard requirements (the app cannot
# run without them) abort with a clear message if auto-install fails.
# Soft requirements (only needed for the shapefile-clip feature) degrade
# gracefully — clipping is simply disabled, the rest of the app still runs.
def _pip_install(*packages):
    pkgs = [p for p in packages if p]
    if not pkgs:
        return True
    print(f"[SETUP] Installing missing package(s): {', '.join(pkgs)} ...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "--quiet", *pkgs]
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[SETUP] pip install failed for {pkgs}: {e}")
        return False


def _ensure(module_name, pip_name=None, required=True):
    pip_name = pip_name or module_name
    if importlib.util.find_spec(module_name) is None:
        ok = _pip_install(pip_name)
        if not ok and required:
            print(
                f"[ERROR] '{module_name}' is required but could not be "
                f"installed automatically.\n"
                f"        Please run manually:  pip install {pip_name}"
            )
            sys.exit(1)


_ensure("requests")
_ensure("tqdm")
for _mod, _pip in (("geopandas", "geopandas"),
                    ("xarray", "xarray"),
                    ("rioxarray", "rioxarray")):
    _ensure(_mod, _pip, required=False)


import re
import tempfile
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Optional geospatial clipping stack — auto-installed above if missing.
# If it still failed (e.g. no internet, unsupported platform), the app
# keeps running with clipping disabled rather than crashing.
try:
    import geopandas as gpd
    import xarray as xr
    import rioxarray  # noqa: F401  (registers the .rio accessor on xarray)
    CLIPPING_AVAILABLE = True
except ImportError:
    CLIPPING_AVAILABLE = False

BUCKET = "nex-gddp-cmip6"
BASE_URL = f"https://{BUCKET}.s3.us-west-2.amazonaws.com"
S3_API = BASE_URL           # same origin, queried via ?list-type=2
ROOT_PREFIX = "NEX-GDDP-CMIP6/"
DOWNLOAD_DIR = "NEX_GDDP"
MAX_WORKERS = 16
XML_NS = "http://s3.amazonaws.com/doc/2006-03-01/"

BANNER = r"""
  ██████╗ ██╗   ██╗██╗     ██████╗
 ██╔════╝ ██║   ██║██║     ██╔══██╗
 ██║  ███╗██║   ██║██║     ██████╔╝
 ██║   ██║██║   ██║██║     ██╔═══╝
 ╚██████╔╝╚██████╔╝███████╗██║
  ╚═════╝  ╚═════╝ ╚══════╝╚═╝

  GDDP Unified Loader & Processor
  NASA NEX-GDDP-CMIP6  |  v1.0.0
"""


# --------------------------------------------------
# S3 REST XML listing  (no JS needed, no auth needed)
# --------------------------------------------------

def s3_list(prefix, delimiter="/"):
    """
    Call the S3 ListObjectsV2 REST API for the given prefix.
    Returns (common_prefixes, object_keys) — both as lists of strings.
    Handles pagination automatically via continuation tokens.
    """
    common_prefixes = []
    object_keys = []
    continuation = None

    while True:
        params = {
            "list-type": "2",
            "prefix":    prefix,
            "delimiter": delimiter,
            "max-keys":  "1000",
        }
        if continuation:
            params["continuation-token"] = continuation

        try:
            r = requests.get(S3_API, params=params, timeout=60)
            r.raise_for_status()
        except Exception as e:
            print(f"[WARN] S3 listing failed for prefix '{prefix}': {e}")
            break

        try:
            root = ET.fromstring(r.content)
        except ET.ParseError as e:
            print(f"[WARN] XML parse error for prefix '{prefix}': {e}")
            break

        ns = {"s3": XML_NS}

        for cp in root.findall("s3:CommonPrefixes/s3:Prefix", ns):
            common_prefixes.append(cp.text)

        for obj in root.findall("s3:Contents/s3:Key", ns):
            object_keys.append(obj.text)

        trunc = root.find("s3:IsTruncated", ns)
        if trunc is not None and trunc.text.lower() == "true":
            tok = root.find("s3:NextContinuationToken", ns)
            continuation = tok.text if tok is not None else None
            if not continuation:
                break
        else:
            break

    return common_prefixes, object_keys


# --------------------------------------------------
# Models
# --------------------------------------------------

def get_models():
    prefixes, _ = s3_list(ROOT_PREFIX, delimiter="/")
    models = []
    for p in prefixes:
        # p looks like "NEX-GDDP-CMIP6/ACCESS-CM2/"
        name = p.rstrip("/").split("/")[-1]
        if name:
            models.append(name)
    return sorted(set(models))


# --------------------------------------------------
# Folder / file helpers
# --------------------------------------------------

def list_folders(s3_prefix):
    """Return bare subfolder names under the given S3 prefix."""
    prefixes, _ = s3_list(s3_prefix, delimiter="/")
    result = []
    for p in prefixes:
        name = p.rstrip("/").split("/")[-1]
        if name:
            result.append(name)
    return sorted(set(result))


def list_nc_files(s3_prefix):
    """Return bare .nc filenames under the given S3 prefix."""
    _, keys = s3_list(s3_prefix, delimiter="/")
    result = []
    for k in keys:
        fname = k.split("/")[-1]
        if fname.endswith(".nc"):
            result.append(fname)
    return result


def extract_version(fname):
    m = re.search(r"_v(\d+\.\d+)\.nc$", fname)
    return ("v" + m.group(1)) if m else "base"


# --------------------------------------------------
# Scan model
# --------------------------------------------------

def scan_model(model):
    print(f"  Scanning {model} ...")
    result = []
    model_prefix = f"{ROOT_PREFIX}{model}/"

    for scenario in list_folders(model_prefix):
        scen_prefix = f"{model_prefix}{scenario}/"

        for realization in list_folders(scen_prefix):
            real_prefix = f"{scen_prefix}{realization}/"

            for variable in list_folders(real_prefix):
                var_prefix = f"{real_prefix}{variable}/"
                files = list_nc_files(var_prefix)
                versions = {extract_version(f) for f in files} or {"base"}

                for version in versions:
                    result.append({
                        "model":       model,
                        "scenario":    scenario,
                        "realization": realization,
                        "variable":    variable,
                        "version":     version,
                    })
    return result


# --------------------------------------------------
# Collect matching files
# --------------------------------------------------

def collect_files(selection):
    files = []
    for item in selection:
        prefix = (f"{ROOT_PREFIX}{item['model']}/{item['scenario']}/"
                  f"{item['realization']}/{item['variable']}/")
        dl_base = f"{BASE_URL}/{prefix}"

        for f in list_nc_files(prefix):
            if extract_version(f) == item["version"]:
                files.append({
                    "url":      dl_base + f,
                    "model":    item["model"],
                    "scenario": item["scenario"],
                    "variable": item["variable"],
                    "file":     f,
                })
    return files


# --------------------------------------------------
# Download
# --------------------------------------------------

def clip_netcdf(in_path, out_path, geometries, geom_crs):
    """
    Open a downloaded NEX-GDDP-CMIP6 NetCDF file, clip it to the given
    shapefile geometries, and write only the clipped (much smaller) result
    to out_path. Raises on failure — caller is responsible for cleanup.
    """
    ds = xr.open_dataset(in_path)
    try:
        # NEX-GDDP-CMIP6 grids are plain WGS84 lat/lon with no CRS metadata.
        ds = ds.rio.set_spatial_dims(x_dim="lon", y_dim="lat")
        ds.rio.write_crs("EPSG:4326", inplace=True)

        # NEX-GDDP-CMIP6 longitude runs 0–360; shapefiles are almost always
        # -180–180. Re-wrap + re-sort so the clip lines up with the geometry
        # instead of silently returning an empty / wrong-side result.
        lon_max = float(ds["lon"].max())
        if lon_max > 180:
            ds = ds.assign_coords(
                lon=(((ds["lon"] + 180) % 360) - 180)
            ).sortby("lon")

        clipped = ds.rio.clip(
            geometries, geom_crs, drop=True, all_touched=True
        )

        encoding = {
            var: {"zlib": True, "complevel": 4}
            for var in clipped.data_vars
        }
        clipped.to_netcdf(out_path, encoding=encoding)
    finally:
        ds.close()


def load_clip_shapefile(path):
    """Read+validate a shapefile, returning (geometries, crs)."""
    gdf = gpd.read_file(path)
    if gdf.empty:
        raise ValueError("Shapefile contains no features.")
    if gdf.crs is None:
        print("[WARN] Shapefile has no CRS — assuming EPSG:4326 (WGS84), "
              "the same system used by the NEX-GDDP-CMIP6 grid.")
        gdf = gdf.set_crs("EPSG:4326")
    print(f"  Loaded shapefile: {len(gdf)} feature(s), CRS: {gdf.crs}")
    return list(gdf.geometry), gdf.crs


def download_file(url, out_file, clip_geom=None, clip_crs=None):
    if os.path.exists(out_file):
        return
    os.makedirs(os.path.dirname(out_file), exist_ok=True)

    tmp_file = None
    download_target = out_file
    if clip_geom is not None:
        fd, tmp_file = tempfile.mkstemp(suffix=".nc", prefix="gulp_raw_")
        os.close(fd)
        download_target = tmp_file

    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(download_target, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"[FAILED] {url}\n  {e}")
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)
        return

    if clip_geom is None:
        return

    try:
        clip_netcdf(tmp_file, out_file, clip_geom, clip_crs)
    except Exception as e:
        print(f"[CLIP FAILED] {out_file}\n  {e}")
        if os.path.exists(out_file):
            os.remove(out_file)
    finally:
        if tmp_file and os.path.exists(tmp_file):
            os.remove(tmp_file)


# --------------------------------------------------
# UI helpers
# --------------------------------------------------

def parse_filter(raw, universe):
    raw = raw.strip()
    if raw.lower() == "all":
        return set(universe)
    return {x.strip() for x in raw.split(",")}


def print_table(rows):
    for i, x in enumerate(rows, 1):
        print(f"  {i:5d}  {x['model']:20s}  {x['scenario']:12s}"
              f"  {x['variable']:12s}  {x['version']:8s}")


# --------------------------------------------------
# MAIN
# --------------------------------------------------

def main():
    print(BANNER)

    # ---- model selection ----
    print("Loading available models...\n")
    models = get_models()
    if not models:
        print("[ERROR] Could not retrieve model list. Check network / URL.")
        sys.exit(1)

    for i, m in enumerate(models, 1):
        print(f"  {i:3d}  {m}")

    sel_raw = input("\nSelect model numbers (comma-separated, e.g. 1,3,5): ")
    try:
        idx = [int(x.strip()) for x in sel_raw.split(",")]
        selected_models = [models[i - 1] for i in idx]
    except (ValueError, IndexError):
        print("[ERROR] Invalid selection.")
        sys.exit(1)

    # ---- scan ----
    print()
    master = []
    for m in selected_models:
        master.extend(scan_model(m))

    if not master:
        print("[ERROR] No combinations found for selected models.")
        sys.exit(1)

    print("\n" + "=" * 72)
    print("  AVAILABLE COMBINATIONS")
    print("=" * 72)
    print_table(master)

    print("\n  Scenarios :", sorted(set(x["scenario"] for x in master)))
    print("  Variables :", sorted(set(x["variable"] for x in master)))
    print("  Versions  :", sorted(set(x["version"] for x in master)))

    # ---- filters ----
    print()
    scen_raw = input("Scenarios (comma-separated or 'all'): ")
    var_raw = input("Variables (comma-separated or 'all'): ")
    ver_raw = input("Versions  (comma-separated or 'all'): ")

    scenarios = parse_filter(scen_raw, set(x["scenario"] for x in master))
    variables = parse_filter(var_raw,  set(x["variable"] for x in master))
    versions = parse_filter(ver_raw,  set(x["version"] for x in master))

    selection = [
        x for x in master
        if x["scenario"] in scenarios
        and x["variable"] in variables
        and x["version"] in versions
    ]

    # ---- summary ----
    print("\n" + "=" * 72)
    print("  DOWNLOAD SUMMARY")
    print("=" * 72)
    print(f"  Combinations : {len(selection)}")

    files = collect_files(selection)
    print(f"  Files found  : {len(files)}")

    if not files:
        print("\n[INFO] Nothing to download.")
        sys.exit(0)

    ans = input("\nProceed with download? [y/n]: ")
    if ans.strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

    # ---- clip prompt ----
    clip_geom, clip_crs = None, None
    print("\n" + "=" * 72)
    print("  CLIP TO SHAPEFILE")
    print("=" * 72)
    print("  Each NetCDF file is roughly 250MB. If you only need data for a")
    print("  specific region, you can clip every file to a shapefile boundary")
    print("  -- only the clipped (much smaller) result is kept, the full")
    print("  download is discarded after clipping.")
    if not CLIPPING_AVAILABLE:
        print("\n  [WARN] Clipping requires 'geopandas', 'xarray' and "
              "'rioxarray'.")
        print("         Install with: pip install geopandas xarray rioxarray")
        print("         Continuing with full-file downloads.\n")
    else:
        clip_ans = input(
            "\nClip files to a shapefile before saving? [y/n]: ")
        if clip_ans.strip().lower() == "y":
            shp_path = input(
                "Path to shapefile (.shp): ").strip().strip('"')
            if not os.path.isfile(shp_path):
                print(f"[ERROR] File not found: {shp_path}")
                sys.exit(1)
            try:
                clip_geom, clip_crs = load_clip_shapefile(shp_path)
            except Exception as e:
                print(f"[ERROR] Could not read shapefile: {e}")
                sys.exit(1)

    # ---- download ----
    tasks = [
        (f["url"],
         os.path.join(DOWNLOAD_DIR, f["model"], f["scenario"],
                      f["variable"], f["file"]))
        for f in files
    ]

    print(
        f"\nDownloading {len(tasks)} file(s) with {MAX_WORKERS} workers...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_file, url, out, clip_geom, clip_crs)
                   for url, out in tasks]
        for fut in tqdm(futures, total=len(futures), unit="file"):
            fut.result()

    print("\n✓  All downloads completed.")
    print(f"  Output directory: {os.path.abspath(DOWNLOAD_DIR)}\n")


if __name__ == "__main__":
    main()
