Set environmental variables for Copernicus username and password:

```
export COPERNICUS_USER="username"
export COPERNICUS_PASS="password"
```

download\_s2\_bands.py uses environmental variables (COPERNICUS\_USER, COPERNICUS\_PASS). You can also specify the download directory when you run this file, but I have it defaulting to ~/scr10/satellite\_stats.

`python download_s2_bands.py c1 c2 c3 c4 yyyy-mm-dd yyyy-mm-dd`

Set JOB\_DIR variable to point to the last\_job.txt file, which is placed where the downloaded data is. This keeps track of the most recently ran job so the user will not need to specify the specific job file when using log\_raw\_bands.py. 

```
JOB_DIR=$(cat ~/scr10/satellite_stats/last_job.txt)
python log_raw_bands.py "$JOB_DIR" --multi
```


I also set up my conda environment with the following:
```
module load miniforge3/24.9.2-0
source "$(conda info --base)/etc/profile.d/conda.sh"
conda create -n sat-stats-env python=3.11
conda activate sat-stats-env
conda install -c conda-forge rasterio numpy requests
conda install -c conda-forge libgdal-jp2openjpeg
```
