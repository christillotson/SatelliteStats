download\_s2\_bands.py uses environmental variables (COPERNICUS\_USER, COPERNICUS\_PASS, S2\_DOWNLOAD\_DIR). You can also specify the download directory when you run this file. 

`python download_s2_bands.py c1 c2 c3 c4 yyyy-mm-dd yyyy-mm-dd`

Set JOB\_DIR variable to point to the last\_job.txt file, which is placed where the downloaded data is. This keeps track of the most recently ran job so the user will not need to specify the specific job file when using log\_raw\_bands.py. 

`python log_raw_bands.py "$JOB_DIR" --multi`


I also set up my conda environment with the following:
```
conda create -n sat-stats-env python=3.11
conda activate sat-stats-env
conda install -c conda-forge rasterio numpy requests
conda install -c conda-forge libgdal-jp2openjpeg
conda install -c conda-forge vim 
```
