# PowerShell Dependency Chaining for Phase 3 Ingestion
# Only run next step if previous succeeds



$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$steps = @(
    'monitor_s3_new_files.ps1',
    'validate_s3_files.ps1',
    'move_to_staging.ps1'
)

foreach ($step in $steps) {
    $stepPath = Join-Path $scriptDir $step
    Write-Output "Running $stepPath..."
    $result = & pwsh $stepPath
    $notifyPath = Join-Path $scriptDir 'notify.ps1'
    if ($LASTEXITCODE -ne 0) {
        & $notifyPath Failure "$step failed. Stopping chain."
        break
    } else {
        & $notifyPath Success "$step completed successfully."
    }
}

# Run ETL after files are staged
$etlPath = Join-Path $scriptDir '..\phase_4_python_etl\etl_main.py'
Write-Output "Running ETL pipeline..."
$etlResult = & pwsh -c "& '..\.venv\Scripts\python.exe' $etlPath"
if ($LASTEXITCODE -ne 0) {
    & $notifyPath Failure "ETL failed. Files remain in staging for investigation."
    Write-Output "ETL failed. Files remain in staging."
    exit 1
} else {
    & $notifyPath Success "ETL completed successfully. Proceeding to archive."
    Write-Output "ETL succeeded. Proceeding to archive."
    $archivePath = Join-Path $scriptDir 'archive_processed_files.ps1'
    $archiveResult = & pwsh $archivePath
    if ($LASTEXITCODE -ne 0) {
        & $notifyPath Failure "Archiving failed after ETL. Files remain in staging."
        Write-Output "Archiving failed after ETL. Files remain in staging."
    } else {
        & $notifyPath Success "Archiving completed after ETL."
        Write-Output "Archiving completed after ETL."
    }
}
