# PowerShell Retry Logic for S3 Operations
param(
    [string]$Bucket,
    [string]$Key,
    [string]$LocalFile,
    [int]$MaxRetries = 3
)

$attempt = 0
while ($attempt -lt $MaxRetries) {
    try {
        $s3 = New-Object -TypeName Amazon.S3.AmazonS3Client
        $s3.GetObject($Bucket, $Key).WriteResponseStreamToFile($LocalFile)
        Write-Output "Success: $Key downloaded from $Bucket."
        break
    } catch {
        $attempt++
        Write-Output "Attempt $attempt failed for $Key."
        if ($attempt -eq $MaxRetries) {
            & ./notify.ps1 Failure "S3 download failed for $Key after $MaxRetries attempts."
            throw $_
        } else {
            Start-Sleep -Seconds 5
        }
    }
}
