"""
log_raw_bands.py
================
Captures a snapshot of raw Sentinel-2 band files BEFORE any index
generation or processing. Run this immediately after download_images.py
and before generate_index_tiffs.py.

Logged per scene
----------------
- scene_name, date, tile, satellite, processing_level  (from folder name)
- cloud_cover_pct          (from embedded MTD XML if present)
- bbox_wgs84               ([min_lon, min_lat, max_lon, max_lat] in WGS-84)
- epsg                     (native CRS of the band files)
- logged_at                (UTC timestamp of when this log was written)
- bands : per-band record
    - file        : filename
    - path        : absolute path
    - size_mb     : file size in MB
    - width/height: pixel dimensions
    - dtype       : rasterio data type string
    - nodata      : nodata sentinel value
    - resolution_m: pixel size in metres (native CRS units assumed metres)
    - stats       : {min, max, mean, std, nodata_pct} sampled from the raw data

Usage
-----
    # Single scene directory
    python log_raw_bands.py <scene_dir>

    # All scene sub-directories under a root
    python log_raw_bands.py <root_dir> --multi

    # Write a CSV alongside the JSON
    python log_raw_bands.py <scene_dir> --csv

    # Custom output path
    python log_raw_bands.py <scene_dir> --out raw_log.json

Dependencies
------------
    pip install rasterio numpy
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from pathlib import Path

import numpy as np
import rasterio
from rasterio.warp import transform_bounds

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BAND_FILES = ["B01", "B02", "B03", "B04", "B05", "B06",
              "B07", "B8A", "B09", "B11", "B12"]

_SCENE_RE = re.compile(
    r"(?P<sat>S2[AB])_"
    r"MSI(?P<level>L[12][AC])_"
    r"(?P<dtstr>\d{8})T\d{6}_"
    r"N\d+_R\d+_"
    r"(?P<tile>T[A-Z0-9]{5})"
)

# ---------------------------------------------------------------------------
# Helpers shared with generate_metadata.py
# ---------------------------------------------------------------------------

def parse_scene_name(name: str) -> dict:
    m = _SCENE_RE.search(name)
    if not m:
        return {"satellite": None, "processing_level": None,
                "date": None, "tile": None}
    raw = m.group("dtstr")
    return {
        "satellite":        m.group("sat"),
        "processing_level": m.group("level"),
        "date":             f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}",
        "tile":             m.group("tile"),
    }


def find_cloud_cover(scene_dir: Path) -> float | None:
    candidates = list(scene_dir.rglob("MTD_MSIL*.xml")) or list(scene_dir.rglob("MTD_TL.xml"))
    if not candidates:
        return None
    try:
        import xml.etree.ElementTree as ET
        root = ET.parse(candidates[0]).getroot()
        ns = re.match(r"\{.*\}", root.tag)
        ns_str = ns.group(0) if ns else ""
        for tag in ("Cloud_Coverage_Assessment", "CLOUD_COVERAGE_ASSESSMENT"):
            el = root.find(f".//{ns_str}{tag}")
            if el is not None and el.text:
                return float(el.text)
    except Exception:
        pass
    return None


def read_bbox_wgs84(path: Path):
    with rasterio.open(path) as src:
        crs = src.crs
        bounds = src.bounds
        epsg = crs.to_epsg() if crs else None
        if crs and crs.to_epsg() != 4326:
            l, b, r, t = transform_bounds(crs, "EPSG:4326", *bounds)
        else:
            l, b, r, t = bounds
    return [round(l, 6), round(b, 6), round(r, 6), round(t, 6)], epsg

# ---------------------------------------------------------------------------
# Per-band snapshot
# ---------------------------------------------------------------------------

def log_band(jp2_path: Path) -> dict:
    """Read a single raw .jp2 band file and return a metadata dict."""
    record = {
        "file":    jp2_path.name,
        "path":    str(jp2_path),
        "size_mb": round(jp2_path.stat().st_size / 1_048_576, 3),
    }
    try:
        with rasterio.open(jp2_path) as src:
            record["width"]        = src.width
            record["height"]       = src.height
            record["dtype"]        = src.dtypes[0]
            record["nodata"]       = src.nodata
            res = src.res  # (pixel_width, pixel_height) in CRS units
            record["resolution_m"] = round(float(res[0]), 2)

            raw = src.read(1).astype(np.float32)

        nodata_val = record["nodata"]
        if nodata_val is not None and not np.isnan(float(nodata_val)):
            mask = raw == float(nodata_val)
        else:
            mask = np.isnan(raw)

        valid = raw[~mask]
        nodata_pct = round(float(mask.sum()) / raw.size * 100, 2)

        if valid.size:
            record["stats"] = {
                "min":        round(float(valid.min()), 4),
                "max":        round(float(valid.max()), 4),
                "mean":       round(float(valid.mean()), 4),
                "std":        round(float(valid.std()), 4),
                "nodata_pct": nodata_pct,
            }
        else:
            record["stats"] = {
                "min": None, "max": None, "mean": None,
                "std": None, "nodata_pct": 100.0,
            }

    except Exception as exc:
        record["error"] = str(exc)

    return record

# ---------------------------------------------------------------------------
# Scene-level snapshot
# ---------------------------------------------------------------------------

def log_scene(scene_dir: Path) -> dict:
    scene_dir = scene_dir.resolve()
    entry = {
        "scene_name": scene_dir.name,
        "scene_dir":  str(scene_dir),
        "logged_at":  datetime.now(timezone.utc).isoformat(),
    }
    entry.update(parse_scene_name(scene_dir.name))
    entry["cloud_cover_pct"] = find_cloud_cover(scene_dir)

    # Locate band files
    band_records = []
    first_jp2 = None
    for band_name in BAND_FILES:
        jp2 = scene_dir / f"{band_name}.jp2"
        if jp2.exists():
            if first_jp2 is None:
                first_jp2 = jp2
            print(f"    Logging {band_name}...", end=" ", flush=True)
            band_records.append({**{"band": band_name}, **log_band(jp2)})
            print("done")
        else:
            band_records.append({
                "band": band_name, "file": f"{band_name}.jp2",
                "present": False,
            })

    entry["bands"] = band_records
    entry["bands_found"]   = sum(1 for b in band_records if b.get("size_mb") is not None)
    entry["bands_missing"] = [b["band"] for b in band_records if not b.get("size_mb")]

    # Spatial info from the first available band
    entry["bbox_wgs84"] = None
    entry["epsg"]       = None
    if first_jp2:
        try:
            entry["bbox_wgs84"], entry["epsg"] = read_bbox_wgs84(first_jp2)
        except Exception as exc:
            entry["bbox_error"] = str(exc)

    return entry

# ---------------------------------------------------------------------------
# Scene discovery
# ---------------------------------------------------------------------------

def discover_scenes(root: Path, multi: bool) -> list[Path]:
    if not multi:
        return [root]
    return [
        p for p in sorted(root.iterdir())
        if p.is_dir() and _SCENE_RE.search(p.name)
    ]

# ---------------------------------------------------------------------------
# CSV export
# ---------------------------------------------------------------------------

def flatten_for_csv(record: dict) -> dict:
    """Top-level scene fields only (band details stay in JSON)."""
    flat = {}
    for k, v in record.items():
        if k == "bands":
            continue  # too nested for a flat CSV row
        elif isinstance(v, list):
            flat[k] = "|".join(str(x) for x in v)
        elif isinstance(v, dict):
            for dk, dv in v.items():
                flat[f"{k}_{dk}"] = dv
        else:
            flat[k] = v
    return flat


def write_csv(records: list[dict], out_path: Path) -> None:
    import csv
    rows = [flatten_for_csv(r) for r in records]
    all_keys = list(dict.fromkeys(k for row in rows for k in row))
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Log raw Sentinel-2 band metadata before index generation."
    )
    parser.add_argument("scene_dir", help="Scene dir (or root if --multi)")
    parser.add_argument("--multi",   action="store_true",
                        help="Treat scene_dir as a root of multiple scenes")
    parser.add_argument("--out",     default=None,
                        help="Output JSON path (default: <scene_dir>/raw_band_log.json)")
    parser.add_argument("--csv",     action="store_true",
                        help="Also write a flattened CSV")
    args = parser.parse_args()

    root = Path(args.scene_dir).resolve()
    if not root.exists():
        print(f"ERROR: '{root}' does not exist.", file=sys.stderr)
        sys.exit(1)

    scenes = discover_scenes(root, args.multi)
    if not scenes:
        print("No scene directories found.", file=sys.stderr)
        sys.exit(1)

    print(f"Logging {len(scenes)} scene(s)...")
    records = []
    for scene_path in scenes:
        print(f"  → {scene_path.name}")
        try:
            records.append(log_scene(scene_path))
        except Exception as exc:
            print(f"    WARNING: failed ({exc})")
            records.append({"scene_name": scene_path.name, "error": str(exc)})

    # Output path
    if args.out:
        out_json = Path(args.out)
    else:
        timestamp = datetime.now(ZoneInfo("America/New_York")).strftime("%Y%m%dT%H%M%S") 
        #out_json = root / f"raw_band_log_{timestamp}.json"
        log_dir = root / "logs"
        log_dir.mkdir(exist_ok = True)
        out_json =  log_dir / f"raw_band_log_{timestamp}.json"

    out_json.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "log_type":     "raw_bands_pre_processing",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scene_count":  len(records),
        "scenes":       records,
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str)
    print(f"\nRaw band log written → {out_json}")

    if args.csv:
        out_csv = out_json.with_suffix(".csv")
        write_csv(records, out_csv)
        print(f"Raw band CSV written → {out_csv}")


if __name__ == "__main__":
    main()
