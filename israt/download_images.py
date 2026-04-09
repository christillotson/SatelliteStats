import os
import sys
import requests
from pathlib import Path

DOWNLOAD_DIR = Path(__file__).resolve().parents[1] / "downloads"
DOWNLOAD_DIR.mkdir(exist_ok=True)

COPERNICUS_USER = os.environ.get("COPERNICUS_USER")
COPERNICUS_PASS = os.environ.get("COPERNICUS_PASS")


def get_token():
    response = requests.post(
        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token",
        data={
            "client_id": "cdse-public",
            "grant_type": "password",
            "username": COPERNICUS_USER,
            "password": COPERNICUS_PASS,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


def download_images(bbox, start_date, end_date, max_cloud_cover=20, max_results=5):
    print("Logging in to Copernicus Data Space...")
    token = get_token()

    min_lon, min_lat, max_lon, max_lat = bbox

    print("Searching for scenes...")
    response = requests.get(
        "https://stac.dataspace.copernicus.eu/v1/collections/sentinel-2-l2a/items",
        params={
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "datetime": f"{start_date}T00:00:00Z/{end_date}T23:59:59Z",
            "limit": max_results,
            "filter-lang": "cql2-text",
            "filter": f"eo:cloud_cover <= {max_cloud_cover}",
        },
    )
    response.raise_for_status()
    features = response.json().get("features", [])

    if not features:
        print("No scenes found. Try adjusting your dates, bbox, or cloud cover.")
        return []

    print(f"Found {len(features)} scenes. Downloading thumbnails...")

    headers = {"Authorization": f"Bearer {token}"}
    downloaded_paths = []

    for feature in features:
        title = feature.get("id", "unknown")
        cloud = feature.get("properties", {}).get("eo:cloud_cover", "?")
        assets = feature.get("assets", {})

        # grab the thumbnail URL from the assets
        thumbnail_url = None
        for key in ["thumbnail", "preview", "overview"]:
            if key in assets:
                thumbnail_url = assets[key].get("href")
                break

        if not thumbnail_url:
            print(f"  No thumbnail available for {title}, skipping.")
            continue

        out_path = DOWNLOAD_DIR / f"{title}_thumbnail.jpg"

        if out_path.exists():
            print(f"  Skipping {title} (already downloaded)")
            downloaded_paths.append(out_path)
            continue

        print(f"  Downloading thumbnail for {title} (cloud cover: {cloud}%)...")
        r = requests.get(thumbnail_url, headers=headers)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            f.write(r.content)
        print(f"  Saved to {out_path}")
        downloaded_paths.append(out_path)

    return downloaded_paths


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print("Usage: python download_images.py min_lon min_lat max_lon max_lat start_date end_date")
        sys.exit(1)

    bbox = tuple(float(x) for x in sys.argv[1:5])
    start, end = sys.argv[5], sys.argv[6]
    paths = download_images(bbox, start, end)
    print("\nDownloaded files:")
    for p in paths:
        print(f"  {p}")
