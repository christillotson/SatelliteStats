#!/bin/bash

#SBATCH --job-name=ndvi_continental_us
#SBATCH --nodes=1 # how many physical machines in the cluster
#SBATCH --ntasks=1 # how many separate 'tasks' (stick to 1)
#SBATCH --cpus-per-task=10 # how many cores (bora max is 20)
#SBATCH --time=1-06:00:00 # d-hh:mm:ss or just No. of minutes
#SBATCH --mem=32G # how much physical memory (all by default)
#SBATCH --mail-type=FAIL,BEGIN,END # when to email you
#SBATCH --mail-user=cttillotson@wm.edu # who to email
#SBATCH -o output/%j.out #STDOUT to file (%j is jobID)
#SBATCH -e output/%j.err #STDERR to file (%j is jobID)

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
DOWNLOAD_DIR="/sciclone/scr10/gzdata440/cttillotson/indices_download"
OUTPUT_DIR="/sciclone/scr10/gzdata440/cttillotson/indices_output"

MIN_LON=-25
MIN_LAT=63
MAX_LON=-13
MAX_LAT=66.5
# DATES ARE IN YYYY-MM-DD
START_DATE="2021-12-25"
END_DATE="2022-12-25"
MAX_RESULTS=1
# max results really shouldn't be higher than ~20 because Copernicus will probably time you out for higher requests. Set lower if you cannot get even this amount
# if you are hitting the maximum of 20, you probably have too big of a job. Try splitting up your requests into multiple different jobs based on your interest
# meaning, closer start/end dates, or smaller bounding box area 
MAX_CLOUD_COVER=10

INDICES=""
# empty string should do all possible indices
# multiple would be structured like INDICES="evi ndvi etc"

# current configuration is max 20 low cloud cover ndvi images across the entire continental US, tried 100 but that failed
# so maybe future implementation will be individual calls of this file, each on specific time / area
# to prevent timeout
# ──────────────────────────────────────────────────────────────────────────────
# ── Credentials ───────────────────────────────────────────────────────────────
ENV_FILE="${1:-.env}"  # default to .env in current dir, or pass a path as argument
if [ ! -f "$ENV_FILE" ]; then
    echo "Error: credentials file not found at '$ENV_FILE'"
    echo "Create it with COPERNICUS_USER and COPERNICUS_PASS, or pass its path as an argument."
    exit 1
fi
set -a
source "$ENV_FILE"
set +a
# ──────────────────────────────────────────────────────────────────────────────

./scripts/make_conda_env.sh
# comment above if running multiple times because it deletes and re-creates the env every time

module load miniforge3
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
