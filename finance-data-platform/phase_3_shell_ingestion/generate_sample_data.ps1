# PowerShell script to generate sample customer and sales data for ingestion testing
$rawDir = "sample_raw_data"
if (!(Test-Path $rawDir)) { New-Item -ItemType Directory -Path $rawDir | Out-Null }

# Generate sample customers.csv
$customers = @(
    "customer_id,first_name,last_name,email",
    "1001,John,Doe,john.doe@example.com",
    "1002,Jane,Smith,jane.smith@example.com"
)
$customers | Set-Content "$rawDir/customers.csv"

# Generate sample sales.csv
$sales = @(
    "sale_id,customer_id,amount,sale_date",
    "2001,1001,15000,2026-02-23",
    "2002,1002,22000,2026-02-23"
)
$sales | Set-Content "$rawDir/sales.csv"

Write-Output "Sample data generated in $rawDir."

# Optionally upload to S3 raw bucket for ingestion test
$RAW_BUCKET = "automotive-raw-data-lerato-2026"
aws s3 cp "$rawDir/customers.csv" "s3://$RAW_BUCKET/customers.csv"
aws s3 cp "$rawDir/sales.csv" "s3://$RAW_BUCKET/sales.csv"
Write-Output "Sample data uploaded to S3 raw bucket."