import os
import sys
import shutil
import zipfile
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

COPERNICUS_USER = os.environ.get("COPERNICUS_USER")
COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS")
# COPERNICUS_USER = None
# COPERNICUS_PASS = None

#DEFAULT_DOWNLOAD_DIR = Path(os.environ.get("S2_DOWNLOAD_DIR", "data/raw")).resolve()
DEFAULT_DOWNLOAD_DIR = Path("~/scr10/satellite_stats").expanduser().resolve()

SENTINEL2_BANDS = [
    "B01", "B02", "B03", "B04", "B05", "B06",
    "B07", "B08", "B8A", "B09", "B11", "B12"
]


def get_token():
    COPERNICUS_USER = os.environ.get("COPERNICUS_USER")
    COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS")
    if not COPERNICUS_USER or not COPERNICUS_PASS:
        raise RuntimeError("Missing COPERNICUS_USER or COPERNICUS_PASS")

    r = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": COPERNICUS_USER,
            "password": COPERNICUS_PASS,
        },
    )
    r.raise_for_status()
    return r.json()["access_token"]


def search_scenes(bbox, start_date, end_date, max_results=1):
    minx, miny, maxx, maxy = bbox
    url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
        f"$filter=Collection/Name eq 'SENTINEL-2' and contains(Name,'MSIL2A') "
        f"and OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({minx} {miny},{maxx} {miny},{maxx} {maxy},{minx} {maxy},{minx} {miny}))') "
        f"and ContentDate/Start gt {start_date}T00:00:00.000Z "
        f"and ContentDate/Start lt {end_date}T00:00:00.000Z"
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

    print("Downloading...")
    r = requests.get(url, headers=headers, stream=True)
    r.raise_for_status()

    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print("Extracting...")
    extract_path.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    zip_path.unlink()
    return extract_path


def find_band_files(extract_path):
    band_files = {}
    for root, _, files in os.walk(extract_path):
        for f in files:
            if "R60m" in root and f.endswith(".jp2"):
                for band in SENTINEL2_BANDS:
                    if f"_{band}_60m" in f or f"_{band}." in f:
                        band_files[band] = Path(root) / f
    return band_files


def download_images(bbox, start, end, max_results=1, download_dir=None):
    download_dir = Path(download_dir) if download_dir else DEFAULT_DOWNLOAD_DIR
    download_dir.mkdir(parents=True, exist_ok=True)

    # Create a timestamped job folder inside the download directory
    timestamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%dT%H%M%S")
    job_dir = download_dir / f"job_{timestamp}"
    job_dir.mkdir(exist_ok=True)
    # record last job name to be used for making the unprocessed data log
    (download_dir / "last_job.txt").write_text(str(job_dir))
    print(f"Job folder: {job_dir}")

    print("Logging in to Copernicus Data Space...")
    token = get_token()

    print("Searching for Sentinel-2 scenes...")
    products = search_scenes(bbox, start, end, max_results=max_results)

    if not products:
        print("No scenes found")
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

        print(f"Found bands: {sorted(band_files.keys())}")

        for band, src in sorted(band_files.items()):
            out_path = scene_dir / f"{band}.jp2"
            shutil.copy2(src, out_path)
            print(f"  {band}: saved -> {out_path}")
            downloaded_paths.append(out_path)

    return downloaded_paths


def main():
    if len(sys.argv) not in (7, 8):
        print("Usage: python scripts/download_images.py min_lon min_lat max_lon max_lat start_date end_date [download_dir]")
        sys.exit(1)

    bbox = tuple(float(x) for x in sys.argv[1:5])
    start = sys.argv[5]
    end = sys.argv[6]
    download_dir = sys.argv[7] if len(sys.argv) == 8 else None

    paths = download_images(bbox, start, end, max_results=1, download_dir=download_dir)

    print("\nDownloaded files:")
    for p in paths:
        print(f"  {p}")


if __name__ == "__main__":
    main()
