#!/bin/bash
set -euo pipefail

./scripts/make_conda_env.sh
# uncomment above when run on hpc just commenting because it takes so long
source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate run-indices-env

python scripts/download_images_unified.py -78 38 -76 39.0 2024-06-01 2024-09-30 4 --max-cloud-cover 20 --download-dir "C:/S2"

JOB_DIR=$(cat "C:/S2/last_job.txt")
JOB_NAME=$(basename "$JOB_DIR")

python scripts/log_raw_bands.py $JOB_DIR --multi

./scripts/do_indices_on_job.sh "$JOB_DIR" "output_tiffs/$JOB_NAME" ndvi
