#!/bin/bash
set -euo pipefail

module load miniforge3
# above line must be uncommented to work on HPC. if commented this should work locally

source "$(conda info --base)/etc/profile.d/conda.sh"

conda env remove -n run-indices-env --yes 2>/dev/null || true
conda env create -f environment.yml
# above line must also refer to where the .yml file is. 
# Because this is run in the same directory as the pipeline, hopefully just environment.yml is good enough

# Verify rasterio loads correctly after creation
conda run -n run-indices-env python -c "import rasterio; print('rasterio OK:', rasterio.__version__)"
