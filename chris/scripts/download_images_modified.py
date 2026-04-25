import os
import sys
import requests
import zipfile
from pathlib import Path

# DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads"
DOWNLOAD_DIR = Path("C:/S2")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# to make it work
# export COPERNICUS_USER="thething"
# export cOPERNICUS_PASS="yougetit"

COPERNICUS_USER = os.environ.get("COPERNICUS_USER")
COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS")

SENTINEL2_BANDS = ["B01", "B02", "B03", "B04", "B05", "B06",
                   "B07", "B08", "B8A", "B09", "B11", "B12"]

def get_token():
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

def search_scenes(bbox, start_date, end_date, max_cloud_cover, max_results):
    minx, miny, maxx, maxy = bbox
    url = (
        "https://catalogue.dataspace.copernicus.eu/odata/v1/Products?"
        f"$filter=Collection/Name eq 'SENTINEL-2' "
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
    print(f"  Downloading ZIP...")
    r = requests.get(url, headers=headers, stream=True)
    with open(zip_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"  Extracting...")
    extract_path = scene_dir / "extracted"
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    zip_path.unlink()  # delete ZIP to save space
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

def download_images(bbox, start_date, end_date, max_cloud_cover=20, max_results=3):
    print("Logging in...")
    token = get_token()

    print("Searching for scenes...")
    products = search_scenes(bbox, start_date, end_date, max_cloud_cover, max_results)

    if not products:
        print("No scenes found. Try adjusting dates, bbox, or cloud cover.")
        return []

    print(f"Found {len(products)} scene(s).")
    downloaded_paths = []

    for product in products:
        product_id = product["Id"]
        title = product["Name"].replace(".SAFE", "")
        print(f"\nScene: {title}")

        scene_dir = DOWNLOAD_DIR / title
        scene_dir.mkdir(exist_ok=True)

        extract_path = download_and_extract(product_id, token, scene_dir)
        band_files = find_band_files(extract_path)

        print(f"  Found bands: {list(band_files.keys())}")
        missing = [b for b in SENTINEL2_BANDS if b not in band_files]
        if missing:
            print(f"  Warning: missing bands: {missing}")

        for band, src_path in band_files.items():
            out_path = scene_dir / f"{band}.jp2"
            src_path.rename(out_path)
            print(f"  {band}: saved → {out_path}")
            downloaded_paths.append(out_path)

    return downloaded_paths

if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python download_images.py min_lon min_lat max_lon max_lat start_date end_date")
        sys.exit(1)

    # python scripts/download_images_modified.py -78 38 -76 39.0 2024-06-01 2024-09-30
    bbox = tuple(float(x) for x in sys.argv[1:5])
    start, end = sys.argv[5], sys.argv[6]
    paths = download_images(bbox, start, end)

    print("\nDownloaded files:")
    for p in paths:
        print(f"  {p}")