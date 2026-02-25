# PowerShell version of monitor_s3_new_files.sh
$RAW_BUCKET = "automotive-raw-data-lerato-2026"
$LOGFILE = "logs/monitor_s3.log"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

 # List all files in the S3 bucket and log them with timestamp, excluding .keep files
$files = aws s3 ls "s3://$RAW_BUCKET/" --recursive | Where-Object { $_ -notmatch ".keep" }
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
foreach ($line in $files) {
    "$date $line" | Out-File -FilePath $LOGFILE -Append
}
# Optionally: add logic to detect new files or trigger downstream scripts
