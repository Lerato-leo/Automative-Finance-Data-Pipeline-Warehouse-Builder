#!/bin/bash
# Idempotency check for S3 ingestion
# Checks if file has already been processed (exists in archive bucket)
RAW_BUCKET="automotive-raw-data-lerato-2026"
ARCHIVE_BUCKET="automotive-archive-data-lerato-2026"
LOGFILE="logs/idempotency_check.log"
mkdir -p logs
aws s3 ls s3://$RAW_BUCKET/ --recursive | awk '{print $4}' | while read -r file; do
    archive_file=$(aws s3 ls s3://$ARCHIVE_BUCKET/ --recursive | grep "$file" | awk '{print $4}')
    if [ "$archive_file" != "" ]; then
        echo "$(date) $file already archived, skipping." >> $LOGFILE
    else
        echo "$(date) $file not archived, ready for processing." >> $LOGFILE
    fi
done
