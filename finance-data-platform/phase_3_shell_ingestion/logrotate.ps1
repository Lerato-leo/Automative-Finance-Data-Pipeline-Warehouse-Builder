# PowerShell Log Rotation Script for Phase 3 Ingestion Logs
# Compresses logs weekly and removes originals

$logDir = "C:\Users\lerat\Documents\Project 4 - Data\Automative-Finance-Data-Pipeline-Warehouse-Builder\finance-data-platform\phase_3_shell_ingestion\logs"
$archiveDir = "$logDir\archive"
$timestamp = Get-Date -Format yyyyMMdd

if (!(Test-Path $archiveDir)) {
    New-Item -ItemType Directory -Path $archiveDir | Out-Null
}

$logs = Get-ChildItem -Path $logDir -Filter "*.log"
if ($logs.Count -gt 0) {
    $archiveFile = "$archiveDir\logs_$timestamp.zip"
    Compress-Archive -Path $logs.FullName -DestinationPath $archiveFile
    Remove-Item $logs.FullName
    Write-Output "Logs archived to $archiveFile and originals removed."
} else {
    Write-Output "No log files found to archive."
}
