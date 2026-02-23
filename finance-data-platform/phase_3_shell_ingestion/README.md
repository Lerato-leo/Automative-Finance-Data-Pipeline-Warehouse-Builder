# Phase 3: Shell Ingestion Pipeline (PowerShell)

## Purpose
Automates the movement, validation, and archiving of raw data files from S3 into a staging area, with notifications and logging. No business logic or transformation occurs here.

## Scripts
- **monitor_s3_new_files.ps1**: Logs all files in the raw S3 bucket.
- **validate_s3_files.ps1**: Validates file format (csv, json, xlsx) and size; sends notifications for each file.
- **move_to_staging.ps1**: Moves valid files from raw to staging; notifies on each file moved or failed.
- **archive_processed_files.ps1**: Archives processed files with timestamped names; notifies on each file archived or failed.
- **notify.ps1**: Sends notifications to Teams/email for each file and step.
- **generate_sample_data.ps1**: Generates and uploads sample data for testing.
- **dependency_chain.ps1**: Orchestrates all steps in sequence, with notifications.

## How It Works
1. **monitor_s3_new_files.ps1** logs all files in the raw bucket.
2. **validate_s3_files.ps1** checks each file for valid format/size and notifies on result.
3. **move_to_staging.ps1** moves valid files to staging and notifies on each file.
4. **archive_processed_files.ps1** archives staged files with a timestamp and notifies on each file.
5. **notify.ps1** is called by each script for Teams/email alerts.
6. **dependency_chain.ps1** runs all steps in order and stops on failure.

## Notifications
- Every file processed triggers a notification (success/failure, file name, step).
- Configure Teams/email in `notification_config_example.txt`.

## Usage
1. Edit `notification_config_example.txt` with your Teams webhook and email SMTP details.
2. Run `generate_sample_data.ps1` to create and upload test data.
3. Run `dependency_chain.ps1` to execute the full ingestion pipeline.

## What This Phase Does NOT Do
- No data cleaning, transformation, or business logic.
- No SCD/upserts or warehouse loading.
- No direct loading into fact/dimension tables.

---
For more, see the main project [README](../../README.md).
