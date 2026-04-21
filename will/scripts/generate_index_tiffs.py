"""
generate_index_tiffs.py
========================
Given a directory of Sentinel-2 60m .jp2 band files,
produces one output GeoTIFF per index defined in Sentinel2Indices.INDICES.

Usage:
    python generate_index_tiffs.py <scene_dir> [output_dir]

Arguments:
    scene_dir    Path to folder containing B01.jp2, B02.jp2, etc.
    output_dir   (Optional) Directory to write results. Defaults to
                 an 'indices' folder inside scene_dir.
"""

# will need to make some kind of environment to make this work - rasterio especially


import sys
import os
import numpy as np
import rasterio
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from Sentinel2Indices import INDICES

# Band order: no B08, no B10
BAND_FILES = ["B01", "B02", "B03", "B04", "B05", "B06",
              "B07", "B8A", "B09", "B11", "B12"]
EXPECTED_BAND_COUNT = len(BAND_FILES)  # 11

def load_bands(scene_dir: str) -> tuple[list[np.ndarray], dict]:
    """Load each band .jp2 in order, return arrays and the rasterio profile."""
    bands = []
    profile = None
    for band_name in BAND_FILES:
        jp2_path = os.path.join(scene_dir, f"{band_name}.jp2")
        if not os.path.exists(jp2_path):
            raise FileNotFoundError(f"Missing band file: {jp2_path}")
        with rasterio.open(jp2_path) as src:
            if profile is None:
                profile = src.profile
            bands.append(src.read(1).astype(np.float32))
    return bands, profile

def build_output_profile(src_profile: dict) -> dict:
    profile = src_profile.copy()
    profile.update(
        driver="GTiff",  # add this
        dtype=rasterio.float32,
        count=1,
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        zlevel=6,
    )
    return profile

def process(scene_dir: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading bands from '{scene_dir}'...")
    bands, profile = load_bands(scene_dir)
    print(f"  Loaded {len(bands)} bands: {BAND_FILES}")
    out_profile = build_output_profile(profile)

    for index_func in INDICES:
        name = index_func.__name__
        out_path = os.path.join(output_dir, f"{name}.tiff")
        print(f"  Computing {name}...", end=" ")
        index_array = index_func(*bands).astype(np.float32)
        with rasterio.open(out_path, "w", **out_profile) as dst:
            dst.write(index_array, 1)
        print(f"saved → {out_path}")

    print(f"\nDone. {len(INDICES)} index GeoTIFFs written to '{output_dir}'.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_index_tiffs.py <scene_dir> [output_dir]")
        sys.exit(1)

    scene_directory = sys.argv[1]
    output_directory = sys.argv[2] if len(sys.argv) >= 3 else os.path.join(scene_directory, "indices")

    process(scene_directory, output_directory)

# python scripts/generate_index_tiffs.py "C:\S2\S2B_MSIL2A_20240623T154819_N0510_R054_T18SUJ_20240623T195821" "output_tiffs"
