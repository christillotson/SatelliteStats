import os
import sys
import json
import numpy as np
import rasterio
from pathlib import Path
from datetime import datetime, timezone

from Sentinel2Indices import INDICES

BAND_FILES = ["B01", "B02", "B03", "B04", "B05", "B06",
              "B07", "B8A", "B09", "B11", "B12"]


INDEX_DESCRIPTIONS = {
    "ndvi":  "Normalized Difference Vegetation Index",
    "evi":   "Enhanced Vegetation Index",
    "savi":  "Soil-Adjusted Vegetation Index",
    "msavi": "Modified Soil-Adjusted Vegetation Index",
    "ndre":  "Normalized Difference Red Edge",
    "reci":  "Red Edge Chlorophyll Index",
    "cire":  "Chlorophyll Index Red Edge",
    "gndvi": "Green NDVI",
    "ndwi":  "Normalized Difference Water Index",
    "mndwi": "Modified NDWI",
    "ndmi":  "Normalized Difference Moisture Index",
    "nbr":   "Normalized Burn Ratio",
    "nbr2":  "Normalized Burn Ratio 2",
    "ndbi":  "Normalized Difference Built-up Index",
    "bsi":   "Bare Soil Index",
    "ui":    "Urban Index",
    "ndsi":  "Normalized Difference Snow Index",
    "ri":    "Redness Index",
}


def load_bands(scene_dir):
    bands = []
    for band_name in BAND_FILES:
        path = os.path.join(scene_dir, f"{band_name}.jp2")
        if not os.path.exists(path):
            raise FileNotFoundError(path)

        with rasterio.open(path) as src:
            bands.append(src.read(1).astype(np.float32))

    return bands


def compute_stats(arr):
    valid = arr[np.isfinite(arr)]

    if valid.size == 0:
        return {
            "min": None,
            "max": None,
            "mean": None,
            "std": None,
            "valid_pct": 0.0,
        }

    return {
        "min": float(np.min(valid)),
        "max": float(np.max(valid)),
        "mean": float(np.mean(valid)),
        "std": float(np.std(valid)),
        "valid_pct": float(valid.size / arr.size * 100),
    }


def process(scene_dir, output_json):
    print(f"Loading bands from {scene_dir}...")
    bands = load_bands(scene_dir)

    metadata = {
        "scene_dir": str(Path(scene_dir).resolve()),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "indices": {}
    }

    for func in INDICES:
        name = func.__name__
        print(f"Computing {name}...")

        arr = func(*bands)

        stats = compute_stats(arr)

        metadata["indices"][name] = {
            "description": INDEX_DESCRIPTIONS.get(name, ""),
            "formula": func.__doc__.strip() if func.__doc__ else "",
            "stats": stats
        }

    with open(output_json, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\nSaved JSON → {output_json}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_index_stats_json.py <scene_dir> [output.json]")
        sys.exit(1)

    scene_dir = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "index_stats.json"

    process(scene_dir, output_json)