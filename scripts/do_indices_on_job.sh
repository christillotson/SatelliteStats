#!/bin/bash
set -euo pipefail

DOWNLOAD_JOB_DIR=$1
OUTPUT_JOB_DIR=$2
INDEX_LIST="${@:3}"  # Captures all arguments from $3 onwards

source "$(conda info --base)/etc/profile.d/conda.sh"

conda activate run-indices-env

echo "Python: $(which python)"
echo "CONDA_PREFIX: $CONDA_PREFIX"

for S2_DIR in "$DOWNLOAD_JOB_DIR"/S2*/; do
    # Skip if not a directory
    [ -d "$S2_DIR" ] || continue

    echo "Looking in: $DOWNLOAD_JOB_DIR for S2* dirs"
    # Extract just the folder name (e.g. S2B_MSIL2A_...)
    FOLDER_NAME=$(basename "$S2_DIR")

    # Mirror the S2B folder name in the output dir
    OUTPUT_DIR="$OUTPUT_JOB_DIR/$FOLDER_NAME"
    mkdir -p "$OUTPUT_DIR"

    # Build the command
    PYTHON="$(which python)"


    CMD=("$PYTHON" ./scripts/generate_index_tiffs.py "$S2_DIR" "$OUTPUT_DIR")

    # Append --indices only if any were provided
    if [ -n "$INDEX_LIST" ]; then
        CMD+=(--indices $INDEX_LIST)
    fi

    echo "Processing: $FOLDER_NAME"
    "${CMD[@]}"
done

conda deactivate

# Without indices (--indices omitted)
#./do_indices_on_job.sh /data/downloads /data/outputs

# With indices
#./do_indices_on_job.sh /data/downloads /data/outputs ndvi evi savi

# ./scripts/do_indices_on_job.sh C:/S2 output_tiffs ndvi
