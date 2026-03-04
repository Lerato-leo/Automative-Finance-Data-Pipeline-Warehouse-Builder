[CmdletBinding()]
param(
    [string]$RawBucket,
    [string]$QueueName,
    [string]$Region,
    [string]$PrefixFilter,
    [string]$EnvFilePath
)

$ErrorActionPreference = "Stop"

$rawBucketEnv = [Environment]::GetEnvironmentVariable("RAW_BUCKET")
$regionEnv = [Environment]::GetEnvironmentVariable("AWS_DEFAULT_REGION")

if ([string]::IsNullOrWhiteSpace($QueueName)) {
    $QueueName = "automotive-raw-s3-events"
}

if ([string]::IsNullOrWhiteSpace($PrefixFilter)) {
    $PrefixFilter = ""
}

if ([string]::IsNullOrWhiteSpace($EnvFilePath)) {
    $EnvFilePath = "../../.env"
}

if ([string]::IsNullOrWhiteSpace($RawBucket) -and -not [string]::IsNullOrWhiteSpace($rawBucketEnv)) {
    $RawBucket = $rawBucketEnv
}

if ([string]::IsNullOrWhiteSpace($Region)) {
    if (-not [string]::IsNullOrWhiteSpace($regionEnv)) {
        $Region = $regionEnv
    }
    else {
        $Region = "us-east-1"
    }
}

function Test-CommandAvailable {
    param([string]$Command)

    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Invoke-AwsText {
    param(
        [string[]]$Arguments
    )

    $result = & aws @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI command failed: aws $($Arguments -join ' ')`n$result"
    }

    return ($result | Out-String).Trim()
}

function Set-OrAppendEnvValue {
    param(
        [string]$Path,
        [string]$Key,
        [string]$Value
    )

    if (-not (Test-Path $Path)) {
        "$Key=$Value" | Out-File -FilePath $Path -Encoding utf8
        return
    }

    $content = Get-Content -Path $Path
    $pattern = "^\s*$([Regex]::Escape($Key))\s*="
    $updated = $false

    for ($i = 0; $i -lt $content.Count; $i++) {
        if ($content[$i] -match $pattern) {
            $content[$i] = "$Key=$Value"
            $updated = $true
            break
        }
    }

    if (-not $updated) {
        $content += "$Key=$Value"
    }

    Set-Content -Path $Path -Value $content -Encoding utf8
}

if (-not (Test-CommandAvailable -Command "aws")) {
    throw "Required command 'aws' not found. Install AWS CLI and ensure it is on PATH."
}

if ([string]::IsNullOrWhiteSpace($RawBucket)) {
    throw "Raw bucket is required. Pass -RawBucket or set RAW_BUCKET in environment/.env."
}

Write-Host "[1/6] Resolving AWS account context..."
$accountId = Invoke-AwsText -Arguments @("sts", "get-caller-identity", "--query", "Account", "--output", "text", "--region", $Region)
$bucketArn = "arn:aws:s3:::$RawBucket"

Write-Host "[2/6] Ensuring SQS queue exists: $QueueName"
$queueUrl = ""
try {
    $queueUrl = Invoke-AwsText -Arguments @("sqs", "get-queue-url", "--queue-name", $QueueName, "--query", "QueueUrl", "--output", "text", "--region", $Region)
}
catch {
    Write-Host "Queue not found. Creating queue..."
    $queueUrl = Invoke-AwsText -Arguments @("sqs", "create-queue", "--queue-name", $QueueName, "--query", "QueueUrl", "--output", "text", "--region", $Region)
}

$queueArn = Invoke-AwsText -Arguments @("sqs", "get-queue-attributes", "--queue-url", $queueUrl, "--attribute-names", "QueueArn", "--query", "Attributes.QueueArn", "--output", "text", "--region", $Region)

Write-Host "[3/6] Applying SQS queue policy for S3 bucket publish rights..."
$policy = @{
    Version   = "2012-10-17"
    Statement = @(
        @{
            Sid       = "AllowS3SendMessage"
            Effect    = "Allow"
            Principal = @{ Service = "s3.amazonaws.com" }
            Action    = "sqs:SendMessage"
            Resource  = $queueArn
            Condition = @{
                ArnEquals    = @{ "aws:SourceArn" = $bucketArn }
                StringEquals = @{ "aws:SourceAccount" = $accountId }
            }
        }
    )
}
$policyJson = $policy | ConvertTo-Json -Depth 10 -Compress
$attributesObject = @{ Policy = $policyJson }
$attributesJson = $attributesObject | ConvertTo-Json -Depth 10 -Compress

$attributesFile = Join-Path $env:TEMP "sqs-attributes-$([Guid]::NewGuid().ToString()).json"
$attributesJson | Out-File -FilePath $attributesFile -Encoding utf8
try {
    Invoke-AwsText -Arguments @("sqs", "set-queue-attributes", "--queue-url", $queueUrl, "--attributes", "file://$attributesFile", "--region", $Region) | Out-Null
}
finally {
    if (Test-Path $attributesFile) {
        Remove-Item $attributesFile -Force
    }
}

Write-Host "[4/6] Configuring S3 bucket notification to SQS..."
$queueConfig = @{
    Id       = "raw-bucket-object-created-to-sqs"
    QueueArn = $queueArn
    Events   = @("s3:ObjectCreated:*")
}

if (-not [string]::IsNullOrWhiteSpace($PrefixFilter)) {
    $queueConfig["Filter"] = @{
        Key = @{
            FilterRules = @(
                @{ Name = "prefix"; Value = $PrefixFilter }
            )
        }
    }
}

$notificationConfig = @{
    QueueConfigurations = @($queueConfig)
}
$notificationJson = $notificationConfig | ConvertTo-Json -Depth 12

$notificationFile = Join-Path $env:TEMP "s3-notification-$([Guid]::NewGuid().ToString()).json"
$notificationJson | Out-File -FilePath $notificationFile -Encoding utf8
try {
    Invoke-AwsText -Arguments @("s3api", "put-bucket-notification-configuration", "--bucket", $RawBucket, "--notification-configuration", "file://$notificationFile", "--region", $Region) | Out-Null
}
finally {
    if (Test-Path $notificationFile) {
        Remove-Item $notificationFile -Force
    }
}

Write-Host "[5/6] Updating .env with queue URL..."
Set-OrAppendEnvValue -Path $EnvFilePath -Key "RAW_S3_EVENTS_QUEUE_URL" -Value $queueUrl

Write-Host "[6/6] Completed successfully"
Write-Host ""
Write-Host "Raw bucket:                $RawBucket"
Write-Host "SQS queue name:            $QueueName"
Write-Host "SQS queue URL:             $queueUrl"
Write-Host "SQS queue ARN:             $queueArn"
Write-Host "Region:                    $Region"
if ($PrefixFilter) {
    Write-Host "Prefix filter:             $PrefixFilter"
}
Write-Host "Updated env file:          $EnvFilePath"
Write-Host ""
Write-Host "Next: Restart Airflow containers so they pick up RAW_S3_EVENTS_QUEUE_URL."
