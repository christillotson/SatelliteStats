# pip install requests numpy rasterio

import os
import io
import requests
import numpy as np
import rasterio
from rasterio.io import MemoryFile
from pathlib import Path

# ── DETECT ENVIRONMENT ────────────────────────────────────────────────────────
HPC_MODE = "SLURM_JOB_ID" in os.environ
print(f"Running in {'HPC' if HPC_MODE else 'laptop'} mode")

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
BBOX   = [-77.55, 37.35, -77.45, 37.45]
START  = "2024-06-01"
END    = "2024-08-01"
WIDTH  = 512
HEIGHT = 512

# ── 1. AUTHENTICATE ───────────────────────────────────────────────────────────
def get_token(username: str, password: str) -> str:
        r = requests.post(
                        "https://identity.dataspace.copernicus.eu/auth/realms/CDSE"
                        "/protocol/openid-connect/token",
                        data={
                            "client_id":  "cdse-public",
                            "username":   username,
                            "password":   password,
                            "grant_type": "password",
                            },
                            timeout=30,
         )
        r.raise_for_status()
        return r.json()["access_token"]


if HPC_MODE:
    USERNAME = os.environ["CDSE_USER"]
    PASSWORD = os.environ["CDSE_PASS"]
else:
    import getpass
    USERNAME = input("CDSE email: ")
    PASSWORD = getpass.getpass("CDSE password: ")

token   = get_token(USERNAME, PASSWORD)
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type":  "application/json",
}
print("Authenticated OK")

# ── 2. FETCH RED + NIR VIA SENTINEL HUB PROCESS API ──────────────────────────
evalscript = """
//VERSION=3
function setup() {
    return {
        input:  [{ bands: ["B04", "B08"], units: "REFLECTANCE" }],
        output: { bands: 2, sampleType: "FLOAT32" }
    };
}
function evaluatePixel(sample) {
    return [sample.B04, sample.B08];
}
"""

payload = {
    "input": {
        "bounds": {
            "bbox": BBOX,
            "properties": {"crs": "http://www.opengis.net/def/crs/EPSG/0/4326"},
        },
        "data": [{
            "dataFilter": {
                "timeRange": {
                    "from": f"{START}T00:00:00Z",
                    "to":   f"{END}T00:00:00Z",
                },
                "maxCloudCoverage": 20,
                "mosaickingOrder": "leastCC",
            },
            "type": "sentinel-2-l2a",
        }],
    },
    "output": {
        "width":  WIDTH,
        "height": HEIGHT,
        "responses": [{"identifier": "default", "format": {"type": "image/tiff"}}],
    },
    "evalscript": evalscript,
}

print(f"Requesting {WIDTH}x{HEIGHT} px image …")
r = requests.post(
    "https://sh.dataspace.copernicus.eu/api/v1/process",
    headers=headers,
    json=payload,
    timeout=120,
)
r.raise_for_status()

# ── 3. DECODE IN MEMORY AND COMPUTE NDVI STATISTICS ──────────────────────────
with MemoryFile(r.content) as memfile:
    with memfile.open() as src:
        red = src.read(1).astype(np.float32)
        nir = src.read(2).astype(np.float32)

denom = nir + red
ndvi  = np.where(denom == 0, np.nan, (nir - red) / denom)

stats = {
    "min":    np.nanmin(ndvi),
    "max":    np.nanmax(ndvi),
    "mean":   np.nanmean(ndvi),
    "median": np.nanmedian(ndvi),
    "std":    np.nanstd(ndvi),
    "valid_pixels":  int(np.sum(~np.isnan(ndvi))),
    "total_pixels":  ndvi.size,
}

print("\n── NDVI Statistics ──────────────────────")
for k, v in stats.items():
    print(f"  {k:<15} {v:.4f}" if isinstance(v, float) else f"  {k:<15} {v}")
print("─────────────────────────────────────────")
