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

MIN_LON=-118
MIN_LAT=32
MAX_LON=-66
MAX_LAT=49.0
START_DATE="2024-06-01"
END_DATE="2024-09-30"
MAX_RESULTS=100
MAX_CLOUD_COVER=10

INDICES="ndvi"

# current configuration is ~100 low cloud cover ndvi images across the entire continental US
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
# uncomment above when run on hpc, just commenting because it takes so long

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
