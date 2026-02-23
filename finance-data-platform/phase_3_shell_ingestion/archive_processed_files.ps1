# PowerShell version of archive_processed_files.sh
$STAGING_BUCKET = "automotive-staging-data-lerato-2026"
$ARCHIVE_BUCKET = "automotive-archive-data-lerato-2026"
$LOGFILE = "logs/archive_processed.log"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }
$TIMESTAMP = Get-Date -Format "yyyyMMddHHmmss"

# List all files in the staging bucket
$files = aws s3 ls "s3://$STAGING_BUCKET/" --recursive | ForEach-Object {
    $_.Split(" ")[-1]
} | Where-Object { $_ -ne "" }

foreach ($file in $files) {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $ext = [System.IO.Path]::GetExtension($file)
    $base = [System.IO.Path]::GetFileNameWithoutExtension($file)
    $archive_file = "$base" + "_" + $TIMESTAMP + $ext
    $copy = aws s3 cp "s3://$STAGING_BUCKET/$file" "s3://$ARCHIVE_BUCKET/$archive_file"
    $notifyPath = Join-Path $PSScriptRoot 'notify.ps1'
    if ($LASTEXITCODE -eq 0) {
        "$date $file archived as $archive_file" | Out-File -FilePath $LOGFILE -Append
        aws s3 rm "s3://$STAGING_BUCKET/$file"
        & $notifyPath Success "File $file archived as $archive_file."
    } else {
        "$date $file FAILED to archive" | Out-File -FilePath $LOGFILE -Append
        & $notifyPath Failure "File $file FAILED to archive."
    }
}
