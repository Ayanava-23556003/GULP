"""
GULP - GeoData Universal Loader for Precipitation
NASA NEX-GDDP-CMIP6 Dataset Downloader
Version 1.0.0
"""

import os
import re
import sys
import xml.etree.ElementTree as ET
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

BUCKET       = "nex-gddp-cmip6"
BASE_URL     = f"https://{BUCKET}.s3.us-west-2.amazonaws.com"
S3_API       = BASE_URL           # same origin, queried via ?list-type=2
ROOT_PREFIX  = "NEX-GDDP-CMIP6/"
DOWNLOAD_DIR = "NEX_GDDP"
MAX_WORKERS  = 16
XML_NS       = "http://s3.amazonaws.com/doc/2006-03-01/"

BANNER = r"""
  ██████╗ ██╗   ██╗██╗     ██████╗
 ██╔════╝ ██║   ██║██║     ██╔══██╗
 ██║  ███╗██║   ██║██║     ██████╔╝
 ██║   ██║██║   ██║██║     ██╔═══╝
 ╚██████╔╝╚██████╔╝███████╗██║
  ╚═════╝  ╚═════╝ ╚══════╝╚═╝

  GeoData Universal Loader for Precipitation
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
    object_keys     = []
    continuation    = None

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
    result       = []
    model_prefix = f"{ROOT_PREFIX}{model}/"

    for scenario in list_folders(model_prefix):
        scen_prefix = f"{model_prefix}{scenario}/"

        for realization in list_folders(scen_prefix):
            real_prefix = f"{scen_prefix}{realization}/"

            for variable in list_folders(real_prefix):
                var_prefix = f"{real_prefix}{variable}/"
                files      = list_nc_files(var_prefix)
                versions   = {extract_version(f) for f in files} or {"base"}

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

def download_file(url, out_file):
    if os.path.exists(out_file):
        return
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    try:
        with requests.get(url, stream=True, timeout=120) as r:
            r.raise_for_status()
            with open(out_file, "wb") as f:
                for chunk in r.iter_content(1024 * 1024):
                    if chunk:
                        f.write(chunk)
    except Exception as e:
        print(f"[FAILED] {url}\n  {e}")


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
    print("  Versions  :", sorted(set(x["version"]  for x in master)))

    # ---- filters ----
    print()
    scen_raw = input("Scenarios (comma-separated or 'all'): ")
    var_raw  = input("Variables (comma-separated or 'all'): ")
    ver_raw  = input("Versions  (comma-separated or 'all'): ")

    scenarios = parse_filter(scen_raw, set(x["scenario"] for x in master))
    variables = parse_filter(var_raw,  set(x["variable"] for x in master))
    versions  = parse_filter(ver_raw,  set(x["version"]  for x in master))

    selection = [
        x for x in master
        if x["scenario"] in scenarios
        and x["variable"] in variables
        and x["version"]  in versions
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

    # ---- download ----
    tasks = [
        (f["url"],
         os.path.join(DOWNLOAD_DIR, f["model"], f["scenario"],
                      f["variable"], f["file"]))
        for f in files
    ]

    print(f"\nDownloading {len(tasks)} file(s) with {MAX_WORKERS} workers...\n")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(download_file, url, out) for url, out in tasks]
        for fut in tqdm(futures, total=len(futures), unit="file"):
            fut.result()

    print("\n✓  All downloads completed.")
    print(f"  Output directory: {os.path.abspath(DOWNLOAD_DIR)}\n")


if __name__ == "__main__":
    main()
