"""
log_outputs.py
==============
For a given job's output directory, produces outputs_log.csv containing
per-tiff metadata including spatial bounds, center, cloud cover, index type,
and source scene.

Usage:
    python scripts/log_outputs.py <output_job_dir> --download-dir <job_download_dir>

Example:
    python scripts/log_outputs.py output_tiffs/job_20260425T185907 \
        --download-dir C:/S2/job_20260425T185907
"""

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime

import rasterio
from rasterio.warp import transform_bounds

OUTPUT_CSV = "outputs_log.csv"
WGS84 = "EPSG:4326"

HEADER = [
    "timestamp",
    "scene_name",
    "index",
    "min_lon", "max_lon",
    "min_lat", "max_lat",
    "center_lon", "center_lat",
    "cloud_cover_pct",
    "crs",
    "resolution_m",
    "width_px", "height_px",
    "tiff_path",
]


def find_metadata_xml(download_job_dir: Path, scene_name: str) -> Path | None:
    """Find MTD_MSIL2A.xml for a given scene name inside the extracted SAFE folder."""
    scene_dir = download_job_dir / scene_name
    extracted = scene_dir / "extracted"
    if not extracted.exists():
        return None
    # SAFE folder name matches scene name
    matches = list(extracted.glob(f"{scene_name}.SAFE/MTD_MSIL2A.xml"))
    if matches:
        return matches[0]
    # Fallback: search anywhere under extracted in case of naming variation
    matches = list(extracted.rglob("MTD_MSIL2A.xml"))
    return matches[0] if matches else None


def parse_cloud_cover(xml_path: Path) -> float | None:
    """Extract cloud cover percentage from MTD_MSIL2A.xml."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # The tag may have a namespace prefix, so search broadly
        for elem in root.iter():
            if elem.tag.endswith("Cloud_Coverage_Assessment"):
                return round(float(elem.text), 2)
    except Exception as e:
        print(f"  Warning: could not parse cloud cover from {xml_path}: {e}")
    return None


def get_tiff_spatial_info(tiff_path: Path) -> dict:
    """Extract bounds, center, CRS, resolution, and dimensions from a GeoTIFF."""
    with rasterio.open(tiff_path) as src:
        native_crs = src.crs
        # Reproject bounds to WGS84 for consistent lat/lon output
        min_lon, min_lat, max_lon, max_lat = transform_bounds(
            native_crs, WGS84,
            src.bounds.left, src.bounds.bottom,
            src.bounds.right, src.bounds.top,
        )
        # Resolution: average x/y in native units (usually metres for UTM)
        res_x, res_y = src.res
        resolution_m = round((abs(res_x) + abs(res_y)) / 2, 2)

        return {
            "min_lon":      round(min_lon, 6),
            "max_lon":      round(max_lon, 6),
            "min_lat":      round(min_lat, 6),
            "max_lat":      round(max_lat, 6),
            "center_lon":   round((min_lon + max_lon) / 2, 6),
            "center_lat":   round((min_lat + max_lat) / 2, 6),
            "crs":          str(native_crs),
            "resolution_m": resolution_m,
            "width_px":     src.width,
            "height_px":    src.height,
        }


def log_outputs(output_job_dir: Path, download_job_dir: Path) -> None:
    output_job_dir = output_job_dir.resolve()
    download_job_dir = download_job_dir.resolve()
    csv_path = output_job_dir / OUTPUT_CSV
    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

    rows = []

    # Each subdirectory in the output job dir is a scene
    scene_dirs = sorted([d for d in output_job_dir.iterdir() if d.is_dir()])
    if not scene_dirs:
        print(f"No scene subdirectories found in {output_job_dir}")
        sys.exit(1)

    for scene_dir in scene_dirs:
        scene_name = scene_dir.name
        tiff_files = sorted(scene_dir.glob("*.tiff"))
        if not tiff_files:
            print(f"  Skipping {scene_name} — no .tiff files found")
            continue

        # Cloud cover from metadata XML
        xml_path = find_metadata_xml(download_job_dir, scene_name)
        if xml_path:
            cloud_cover = parse_cloud_cover(xml_path)
        else:
            print(f"  Warning: no MTD_MSIL2A.xml found for {scene_name}, cloud cover will be empty")
            cloud_cover = None

        for tiff_path in tiff_files:
            index_name = tiff_path.stem  # e.g. "ndvi", "evi"
            print(f"  Processing {scene_name}/{tiff_path.name}...")
            try:
                spatial = get_tiff_spatial_info(tiff_path)
            except Exception as e:
                print(f"    Error reading {tiff_path}: {e}")
                continue

            rows.append({
                "timestamp":      timestamp,
                "scene_name":     scene_name,
                "index":          index_name,
                "min_lon":        spatial["min_lon"],
                "max_lon":        spatial["max_lon"],
                "min_lat":        spatial["min_lat"],
                "max_lat":        spatial["max_lat"],
                "center_lon":     spatial["center_lon"],
                "center_lat":     spatial["center_lat"],
                "cloud_cover_pct": cloud_cover if cloud_cover is not None else "",
                "crs":            spatial["crs"],
                "resolution_m":   spatial["resolution_m"],
                "width_px":       spatial["width_px"],
                "height_px":      spatial["height_px"],
                "tiff_path":      str(tiff_path),
            })

    if not rows:
        print("No output tiffs found to log.")
        sys.exit(1)

    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nLogged {len(rows)} entries → {csv_path}")


def parse_args():
    parser = argparse.ArgumentParser(description="Log output GeoTIFF metadata to CSV.")
    parser.add_argument("output_job_dir", type=Path,
                        help="Path to the job's output directory (e.g. output_tiffs/job_20260425T185907)")
    parser.add_argument("--download-dir", type=Path, required=True,
                        help="Path to the job's download directory (e.g. C:/S2/job_20260425T185907)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    log_outputs(args.output_job_dir, args.download_dir)
