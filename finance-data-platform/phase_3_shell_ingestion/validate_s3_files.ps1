# PowerShell version of validate_s3_files.sh
$RAW_BUCKET = "automotive-raw-data-lerato-2026"
$LOGFILE = "logs/validate_s3.log"
if (!(Test-Path "logs")) { New-Item -ItemType Directory -Path "logs" | Out-Null }

 # List all files in the S3 bucket, excluding .keep files
$files = aws s3 ls "s3://$RAW_BUCKET/" --recursive | ForEach-Object {
    $_.Split(" ")[-1]
} | Where-Object { $_ -ne "" -and $_ -notmatch ".keep" }

foreach ($file in $files) {
    $ext = [System.IO.Path]::GetExtension($file).TrimStart('.')
    $size = aws s3api head-object --bucket $RAW_BUCKET --key "$file" --query 'ContentLength' --output text
    $date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $notifyPath = Join-Path $PSScriptRoot 'notify.ps1'
    if ($ext -in @('csv','json','xlsx') -and [int]$size -gt 0) {
        "$date $file valid ($ext, $size bytes)" | Out-File -FilePath $LOGFILE -Append
        & $notifyPath Success "File $file is valid ($ext, $size bytes)."
    } else {
        "$date $file INVALID ($ext, $size bytes)" | Out-File -FilePath $LOGFILE -Append
        & $notifyPath Failure "File $file INVALID ($ext, $size bytes)."
    }
}
