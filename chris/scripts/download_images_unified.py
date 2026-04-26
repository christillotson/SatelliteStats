"""
download_images_unified.py
==================
Downloads Sentinel-2 L2A scenes from Copernicus Data Space and organises
bands into a timestamped job folder.

Usage:
    python download_images_unified.py <min_lon> <min_lat> <max_lon> <max_lat> \
        <start_date> <end_date> <max_results> \
        [--max-cloud-cover 30] [--download-dir /some/path]

Arguments:
    min_lon, min_lat, max_lon, max_lat   Bounding box (decimal degrees)
    start_date, end_date                 ISO dates e.g. 2024-06-01
    max_results                          Required. Max number of scenes to download.
    --max-cloud-cover                    Optional. 0–100. Default: 30.
    --download-dir                       Optional. Overrides default download location.

Environment variables required:
    COPERNICUS_USER
    COPERNICUS_PASS
"""

import argparse
import os
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DEFAULT_DOWNLOAD_DIR = Path("~/scr10/satellite_stats").expanduser().resolve()

# For chris

# DOWNLOAD_DIR = Path("C:/S2")

SENTINEL2_BANDS = [
    "B01", "B02", "B03", "B04", "B05", "B06",
    "B07", "B08", "B8A", "B09", "B11", "B12",
]


def get_token():
    user = os.environ.get("COPERNICUS_USER")
    password = os.environ.get("COPERNICUS_PASS")
    if not user or not password:
        raise RuntimeError("Missing COPERNICUS_USER or COPERNICUS_PASS environment variables.")

    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": user,
            "password": password,
        },
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_scenes(bbox, start_date, end_date, max_cloud_cover, max_results):
    minx, miny, maxx, maxy = bbox
    polygon = f"{minx} {miny},{maxx} {miny},{maxx} {maxy},{minx} {maxy},{minx} {miny}"
    url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
        "$filter="
        "Collection/Name eq 'SENTINEL-2' "
        "and contains(Name,'MSIL2A') "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({polygon}))') "
        f"and ContentDate/Start gt {start_date}T00:00:00.000Z "
        f"and ContentDate/Start lt {end_date}T00:00:00.000Z "
        f"and Attributes/OData.CSC.DoubleAttribute/any("
        f"att:att/Name eq 'cloudCover' and att/Value le {max_cloud_cover:.1f})"
        f"&$top={max_results}"
    )
    r = requests.get(url)
    r.raise_for_status()
    return r.json().get("value", [])


def download_and_extract(product_id, token, scene_dir):
    url = f"https://download.dataspace.copernicus.eu/odata/v1/Products({product_id})/$value"
    headers = {"Authorization": f"Bearer {token}"}

    zip_path = scene_dir / f"{product_id}.zip"
    extract_path = scene_dir / "extracted"

    print("  Downloading ZIP...")
    r = requests.get(url, headers=headers, stream=True)
    r.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print("  Extracting...")
    extract_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    zip_path.unlink()
    return extract_path


def find_band_files(extract_path):
    """Walk extracted directory and find 60m band files."""
    band_files = {}
    for root, _, files in os.walk(extract_path):
        for f in files:
            if "R60m" in root and f.endswith(".jp2"):
                for band in SENTINEL2_BANDS:
                    if f"_{band}_60m" in f or f"_{band}." in f:
                        band_files[band] = Path(root) / f
    return band_files


def download_images(bbox, start_date, end_date, max_results, max_cloud_cover=30, download_dir=None):
    download_dir = Path(download_dir).resolve() if download_dir else DEFAULT_DOWNLOAD_DIR
    download_dir.mkdir(parents=True, exist_ok=True)

    # Timestamped job folder
    timestamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%dT%H%M%S")
    job_dir = download_dir / f"job_{timestamp}"
    job_dir.mkdir(exist_ok=True)
    (download_dir / "last_job.txt").write_text(str(job_dir))
    print(f"Job folder: {job_dir}")

    print("Logging in to Copernicus Data Space...")
    token = get_token()

    print(f"Searching for scenes (max cloud cover: {max_cloud_cover}%)...")
    products = search_scenes(bbox, start_date, end_date, max_cloud_cover, max_results)

    if not products:
        print("No scenes found. Try adjusting dates, bbox, or cloud cover.")
        return []

    print(f"Found {len(products)} scene(s).")
    downloaded_paths = []

    for product in products:
        title = product["Name"].replace(".SAFE", "")
        scene_dir = job_dir / title
        scene_dir.mkdir(parents=True, exist_ok=True)

        print(f"\nScene: {title}")
        extract_path = download_and_extract(product["Id"], token, scene_dir)
        band_files = find_band_files(extract_path)

        print(f"  Found bands: {sorted(band_files.keys())}")
        missing = [b for b in SENTINEL2_BANDS if b not in band_files]
        if missing:
            print(f"  Warning: missing bands: {missing}")

        for band, src_path in sorted(band_files.items()):
            out_path = scene_dir / f"{band}.jp2"
            shutil.copy2(src_path, out_path)
            print(f"  {band}: saved → {out_path}")
            downloaded_paths.append(out_path)

    return downloaded_paths


def parse_args():
    parser = argparse.ArgumentParser(description="Download Sentinel-2 scenes from Copernicus Data Space.")
    parser.add_argument("min_lon", type=float)
    parser.add_argument("min_lat", type=float)
    parser.add_argument("max_lon", type=float)
    parser.add_argument("max_lat", type=float)
    parser.add_argument("start_date", help="e.g. 2024-06-01")
    parser.add_argument("end_date",   help="e.g. 2024-09-30")
    parser.add_argument("max_results", type=int, help="Maximum number of scenes to download.")
    parser.add_argument("--max-cloud-cover", type=float, default=30,
                        help="Maximum cloud cover percentage (default: 30).")
    parser.add_argument("--download-dir", default=None,
                        help=f"Download directory (default: {DEFAULT_DOWNLOAD_DIR}).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    bbox = (args.min_lon, args.min_lat, args.max_lon, args.max_lat)

    paths = download_images(
        bbox,
        args.start_date,
        args.end_date,
        max_results=args.max_results,
        max_cloud_cover=args.max_cloud_cover,
        download_dir=args.download_dir,
    )

    print("\nDownloaded files:")
    for p in paths:
        print(f"  {p}")