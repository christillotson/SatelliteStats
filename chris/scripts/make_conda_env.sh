#!/bin/bash
set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"

conda env remove -n run-indices-env --yes 2>/dev/null || true
conda env create -f ~/PythonStuff/Automation/Projects/SatelliteStats/chris/environment.yml

# Verify rasterio loads correctly after creation
conda run -n run-indices-env python -c "import rasterio; print('rasterio OK:', rasterio.__version__)"
