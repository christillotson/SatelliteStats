# Sentinel-2 Spectral Index Pipeline

A batch pipeline for downloading Sentinel-2 L2A imagery from the Copernicus Data Space, computing spectral indices, and logging the results. Designed to run on an HPC cluster via SLURM, but usable locally with minor adjustments.

---

## Table of Contents

- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Setup](#setup)
- [Configuration](#configuration)
- [Running the Pipeline](#running-the-pipeline)
- [Pipeline Steps](#pipeline-steps)
- [Available Spectral Indices](#available-spectral-indices)
- [Outputs](#outputs)

---

## Overview

The pipeline performs the following steps in order:

1. Creates a reproducible Conda environment
2. Downloads Sentinel-2 scenes from the Copernicus Data Space API
3. Logs raw band metadata (before any processing)
4. Computes spectral index GeoTIFFs for each scene
5. Logs the job call parameters to a persistent CSV
6. Logs metadata for all output GeoTIFFs to a CSV

---

## Repository Structure

```
.
├── pipeline.slurm                  # Main SLURM job script
├── environment.yml                 # Conda environment definition
├── .env                            # Copernicus credentials (not committed)
├── output/                         # SLURM stdout/stderr logs (auto-created)
└── scripts/
    ├── download_images_unified.py  # Downloads scenes from Copernicus Data Space
    ├── log_raw_bands.py            # Logs raw band metadata before processing
    ├── generate_index_tiffs.py     # Computes and writes spectral index GeoTIFFs
    ├── Sentinel2Indices.py         # Index function definitions
    ├── do_indices_on_job.sh        # Iterates over scenes and calls generate_index_tiffs.py
    ├── log_job_calls.sh            # Appends job parameters to a persistent CSV log
    ├── log_outputs.py              # Logs output GeoTIFF metadata to CSV
    └── make_conda_env.sh           # Creates the Conda environment from environment.yml
```

---

## Prerequisites

- Access to a SLURM HPC cluster with Miniforge3/Conda available as a module, **or** a local Conda installation
- A free [Copernicus Data Space](https://dataspace.copernicus.eu/) account

---

## Setup

**1. Clone the repository and navigate to it:**
```
git clone <repo-url>
cd <repo-dir>
```

**2. Create a `.env` file with your Copernicus credentials:**
```
# .env
COPERNICUS_USER=your_username
COPERNICUS_PASS=your_password
```
This file is sourced automatically by `pipeline.slurm`. Never commit it to version control.

**3. Build the Conda environment:**

On HPC (run once before submitting jobs, or let the pipeline do it):
```
./scripts/make_conda_env.sh
```

The environment is named `run-indices-env` and is defined in `environment.yml`.

---

## Configuration

All job parameters are set at the top of `pipeline.slurm` and must be specified by you in this file:

| Variable | Description | Example |
|---|---|---|
| `DOWNLOAD_DIR` | Root directory where scene ZIPs and bands are saved | `/sciclone/scr10/.../indices_download` |
| `OUTPUT_DIR` | Root directory where index GeoTIFFs are written | `/sciclone/scr10/.../indices_output` |
| `MIN_LON` / `MAX_LON` | Bounding box longitude range (decimal degrees) | `-118` / `-66` |
| `MIN_LAT` / `MAX_LAT` | Bounding box latitude range (decimal degrees) | `32` / `49.0` |
| `START_DATE` / `END_DATE` | Scene search date range (ISO format) | `2024-06-01` / `2024-09-30` |
| `MAX_RESULTS` | Maximum number of scenes to download | `100` |
| `MAX_CLOUD_COVER` | Maximum cloud cover percentage (0–100) | `10` |
| `INDICES` | Space-separated list of index names to compute | `"ndvi evi savi"` |

 
SLURM resource settings are also at the top of the file and should be adjusted to match your cluster's limits and the scale of your job.

**`MAX_RESULTS` should not be more than ~20 scenes as Copernicus will likely timeout for higher requests.** Try splitting requests into multiple different jobs based on interests, such as closer start and end dates or smaller bounding box areas.

---

## Running the Pipeline

**On HPC via SLURM:**
```
sbatch pipeline.slurm
# Or pass a custom credentials file:
sbatch pipeline.slurm /path/to/my.env
```

---

## Pipeline Steps

### 1. Environment Setup — `make_conda_env.sh`
Removes any existing `run-indices-env` environment and recreates it from `environment.yml`. Verifies that `rasterio` imports correctly after installation.

### 2. Download Scenes — `download_images_unified.py`
Queries the Copernicus Data Space OData catalogue for Sentinel-2 L2A scenes matching the configured bounding box, date range, and cloud cover threshold. For each matching scene, downloads the ZIP archive, extracts the 60m-resolution `.jp2` band files, and organises them into a timestamped job folder:

```
<DOWNLOAD_DIR>/
└── job_YYYYMMDDTHHMMSS/
    └── <SCENE_NAME>/
        ├── B01.jp2
        ├── B02.jp2
        └── ...
```

The job folder path is written to `<DOWNLOAD_DIR>/last_job.txt` for use by subsequent steps.

**Bands downloaded:** B01, B02, B03, B04, B05, B06, B07, B08, B8A, B09, B11, B12

### 3. Log Raw Bands — `log_raw_bands.py`
Before any processing, captures a full snapshot of each raw band file. Writes a JSON log to `<job_dir>/logs/raw_band_log_<timestamp>.json` containing per-scene and per-band metadata including file size, pixel dimensions, data type, nodata value, resolution, and basic statistics (min, max, mean, std, nodata percentage). Optionally exports a flattened CSV with `--csv`.

### 4. Generate Index GeoTIFFs — `do_indices_on_job.sh` + `generate_index_tiffs.py`
`do_indices_on_job.sh` iterates over all `S2*` scene directories in the job's download folder and calls `generate_index_tiffs.py` for each one. Output GeoTIFFs are written to a mirrored directory structure under `OUTPUT_DIR`:

```
<OUTPUT_DIR>/
└── job_YYYYMMDDTHHMMSS/
    └── <SCENE_NAME>/
        ├── ndvi.tiff
        ├── evi.tiff
        └── ...
```

Each GeoTIFF is Float32, single-band, deflate-compressed, and preserves the native UTM CRS and geotransform of the source bands.

### 5. Log Job Call — `log_job_calls.sh`
Appends a single row to `job_calls_log.csv` in the working directory recording all parameters used for this job (timestamp, bounding box, dates, cloud cover, indices, download and output paths). Creates the file with a header on first run.

### 6. Log Outputs — `log_outputs.py`
Walks all output GeoTIFFs for the job and writes `outputs_log.csv` inside the job's output directory. Each row records the scene name, index type, WGS-84 bounding box and center coordinates, cloud cover (parsed from the scene's `MTD_MSIL2A.xml`), CRS, resolution, and pixel dimensions.

---

## Available Spectral Indices

All index functions are defined in `Sentinel2Indices.py`. The pipeline uses 11 bands (B01–B12, excluding B08 and B10), all expected as reflectance values in [0, 1].

| Index | Name | Primary Use |
|---|---|---|
| `ndvi` | Normalized Difference Vegetation Index | General vegetation health |
| `evi` | Enhanced Vegetation Index | Vegetation with atmospheric correction |
| `savi` | Soil-Adjusted Vegetation Index | Vegetation over exposed soil |
| `msavi` | Modified Soil-Adjusted Vegetation Index | Low-cover vegetation |
| `reci` | Red Edge Chlorophyll Index | Canopy chlorophyll content |
| `cire` | Chlorophyll Index Red Edge | Chlorophyll via red-edge bands |
| `gndvi` | Green NDVI | Chlorophyll concentration |
| `ndwi` | Normalized Difference Water Index | Surface water extent |
| `mndwi` | Modified NDWI | Water / built-up separation |
| `ndmi` | Normalized Difference Moisture Index | Vegetation water content |
| `nbr` | Normalized Burn Ratio | Post-fire burn severity |
| `nbr2` | Normalized Burn Ratio 2 | Burn severity (SWIR-only) |
| `ndbi` | Normalized Difference Built-up Index | Urban / impervious surfaces |
| `bsi` | Bare Soil Index | Exposed bare soil |
| `ui` | Urban Index | Urban land cover |
| `ndsi` | Normalized Difference Snow Index | Snow / ice cover |
| `ri` | Redness Index | Bare soil / iron-oxide content |
| `fai` | Floating Algae Index | Floating aquatic vegetation |
| `ndre` | Normalized Difference Red Edge | Low-concentration chlorophyll |
| `rededge_chlorophyll` | Red Edge Chlorophyll Index | Aquatic plant chlorophyll |
| `ndwi_aquatic` | NDWI (Aquatic variant) | Water surface / floating vegetation |
| `ci_green` | Green Chlorophyll Index | Chlorophyll-a in water bodies |
| `ndci` | Normalized Difference Chlorophyll Index | Phytoplankton in coastal/inland water |

To run a subset of indices, set the `INDICES` variable in `pipeline.slurm`:
```
INDICES="ndvi evi nbr"
```
To run all indices, leave `INDICES` empty or omit the `--indices` flag when calling `generate_index_tiffs.py` directly.

---

## Outputs

After a successful run, the following files are produced:

| Path | Description |
|---|---|
| `<DOWNLOAD_DIR>/job_<timestamp>/` | Raw band `.jp2` files organised by scene |
| `<DOWNLOAD_DIR>/last_job.txt` | Path to the most recent download job folder |
| `<DOWNLOAD_DIR>/job_<timestamp>/logs/raw_band_log_<timestamp>.json` | Pre-processing band metadata snapshot |
| `<OUTPUT_DIR>/job_<timestamp>/<scene>/` | Output index `.tiff` files per scene |
| `<OUTPUT_DIR>/job_<timestamp>/outputs_log.csv` | Spatial and cloud metadata for all output GeoTIFFs |
| `job_calls_log.csv` | Persistent log of all job parameter sets (appended each run) |
| `output/<slurm_job_id>.out` / `.err` | SLURM stdout and stderr |
