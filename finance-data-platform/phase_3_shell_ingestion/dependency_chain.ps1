# PowerShell Dependency Chaining for Phase 3 Ingestion
# Only run next step if previous succeeds


$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$steps = @(
    'monitor_s3_new_files.ps1',
    'validate_s3_files.ps1',
    'move_to_staging.ps1',
    'archive_processed_files.ps1'
)

foreach ($step in $steps) {
    $stepPath = Join-Path $scriptDir $step
    Write-Output "Running $stepPath..."
    # Run shell scripts using PowerShell's call operator
    $result = & pwsh $stepPath
    $notifyPath = Join-Path $scriptDir 'notify.ps1'
    if ($LASTEXITCODE -ne 0) {
        & $notifyPath Failure "$step failed. Stopping chain."
        break
    } else {
        & $notifyPath Success "$step completed successfully."
    }
}
