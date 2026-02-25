# PowerShell version of move_to_staging.sh
$RAW_BUCKET = "automotive-raw-data-lerato-2026"
$STAGING_BUCKET = "automotive-staging-data-lerato-2026"
$LOGFILE = "logs/move_to_staging.log"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

 # List all files in the raw bucket, excluding .keep files
$files = aws s3 ls "s3://$RAW_BUCKET/" --recursive | ForEach-Object {
    $_.Split(" ")[-1]
} | Where-Object { $_ -ne "" -and $_ -notmatch ".keep" }

foreach ($file in $files) {
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $copy = aws s3 cp "s3://$RAW_BUCKET/$file" "s3://$STAGING_BUCKET/$file"
    $notifyPath = Join-Path $PSScriptRoot 'notify.ps1'
    if ($LASTEXITCODE -eq 0) {
        "$date $file moved to staging" | Out-File -FilePath $LOGFILE -Append
        aws s3 rm "s3://$RAW_BUCKET/$file"
        & $notifyPath Success "File $file moved to staging."
    } else {
        "$date $file FAILED to move" | Out-File -FilePath $LOGFILE -Append
        & $notifyPath Failure "File $file FAILED to move."
    }
}
