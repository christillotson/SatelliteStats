#!/bin/bash
set -euo pipefail

# Arguments passed from pipeline.sh
JOB_NAME=$1
DOWNLOAD_DIR=$2
OUTPUT_DIR=$3
MIN_LON=$4
MIN_LAT=$5
MAX_LON=$6
MAX_LAT=$7
START_DATE=$8
END_DATE=$9
MAX_RESULTS=${10}
MAX_CLOUD_COVER=${11}
INDICES=${12}

LOG_FILE="job_calls_log.csv"
TIMESTAMP=$(date +"%Y-%m-%dT%H:%M:%S")
HEADER="timestamp,job_name,download_dir,output_dir,min_lon,min_lat,max_lon,max_lat,start_date,end_date,max_results,max_cloud_cover,indices"
ROW="$TIMESTAMP,$JOB_NAME,$DOWNLOAD_DIR,$OUTPUT_DIR,$MIN_LON,$MIN_LAT,$MAX_LON,$MAX_LAT,$START_DATE,$END_DATE,$MAX_RESULTS,$MAX_CLOUD_COVER,$INDICES"

if [ ! -f "$LOG_FILE" ]; then
    echo "$HEADER" > "$LOG_FILE"
fi

echo "$ROW" >> "$LOG_FILE"
echo "Logged job call → $LOG_FILE"
