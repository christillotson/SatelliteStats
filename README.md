# SatelliteStats

## Conda environment setup

The conda environment can be set up with the following commands:
```
module load miniforge3/24.9.2-0
source "$(conda info --base)/etc/profile.d/conda.sh"
conda create -n sat-stats-env python=3.11
conda activate sat-stats-env
conda install -c conda-forge rasterio numpy requests
conda install -c conda-forge libgdal-jp2openjpeg
```


## Downloading data and getting image statistics/information before processing

Set environmental variables for Copernicus username and password:

```
export COPERNICUS_USER="username"
export COPERNICUS_PASS="password"
```

download\_s2\_bands.py uses these environmental variables (COPERNICUS\_USER, COPERNICUS\_PASS). You can also specify the download directory (\[download\_dir\]) when you run this file, but this is optional, and the default location is ~/scr10/satellite\_stats.

`python download_s2_bands.py min_lon min_lat max_lon max_lat yyyy-mm-dd yyyy-mm-dd [download_dir]`

Set the JOB\_DIR variable to point to the contents of the last\_job.txt file, which is placed in the same directory as the downloaded data. This keeps track of the most recently run job so the user will not need to specify the job file name when using log\_raw\_bands.py. If you download data in another directory besides ~/scr10/satellite\_stats/, then you will need to change this first line below:

```
JOB_DIR=$(cat ~/scr10/satellite_stats/last_job.txt)
python log_raw_bands.py "$JOB_DIR" --multi
```

The JOB\_DIR variable is not needed in the log\_raw\_bands.py file if you want to get a log for a specific job that is not the most recent one (you would just need to replace “$JOB\_DIR” with the desired job directory).


