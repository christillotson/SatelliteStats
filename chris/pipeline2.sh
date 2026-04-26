#!/bin/bash
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
DOWNLOAD_DIR="C:/S2"
OUTPUT_DIR="output_tiffs"

MIN_LON=-78
MIN_LAT=38
MAX_LON=-76
MAX_LAT=39.0
START_DATE="2024-06-01"
END_DATE="2024-09-30"
MAX_RESULTS=1
MAX_CLOUD_COVER=20

INDICES="ndvi evi"
# ──────────────────────────────────────────────────────────────────────────────

./scripts/make_conda_env.sh
# uncomment above when run on hpc, just commenting because it takes so long
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate run-indices-env

python scripts/download_images_unified.py \
    $MIN_LON $MIN_LAT $MAX_LON $MAX_LAT \
    $START_DATE $END_DATE $MAX_RESULTS \
    --max-cloud-cover $MAX_CLOUD_COVER \
    --download-dir "$DOWNLOAD_DIR"

JOB_DIR=$(cat "$DOWNLOAD_DIR/last_job.txt")
JOB_NAME=$(basename "$JOB_DIR")

python scripts/log_raw_bands.py "$JOB_DIR" --multi
./scripts/do_indices_on_job.sh "$JOB_DIR" "$OUTPUT_DIR/$JOB_NAME" $INDICES

./scripts/log_job_calls.sh \
    "$JOB_NAME" "$DOWNLOAD_DIR" "$OUTPUT_DIR" \
    $MIN_LON $MIN_LAT $MAX_LON $MAX_LAT \
    $START_DATE $END_DATE $MAX_RESULTS $MAX_CLOUD_COVER "$INDICES"

python scripts/log_outputs.py "$OUTPUT_DIR/$JOB_NAME" --download-dir "$JOB_DIR"
