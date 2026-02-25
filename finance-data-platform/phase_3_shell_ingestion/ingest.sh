#!/bin/bash
# Robust shell ingestion script for S3 files (CSV/XLSX/JSON)
# Moves only files (not folders) from raw to staging, based on primary format

set -e

RAW_BUCKET="automotive-raw-data-lerato-2026"
STAGING_BUCKET="automotive-staging-data-lerato-2026"

# Entity config: name, source prefix, extension, destination prefix
entities=(
  "customers erp/customers/customers_2026 .xlsx staging/erp/customers/"
  "dealers erp/dealers/dealers_2026 .xlsx staging/erp/dealers/"
  "sales erp/sales/sales_2026 .csv staging/erp/sales/"
  "vehicles erp/vehicles/vehicles_2026 .csv staging/erp/vehicles/"
  "inventory erp/inventory/inventory_2026 .csv staging/erp/inventory/"
  "payments finance/payments/payments_2026 .csv staging/finance/payments/"
  "suppliers suppliers_chain/suppliers/suppliers_2026 .csv staging/suppliers_chain/suppliers/"
  "procurement suppliers_chain/procurement/procurement_2026 .csv staging/suppliers_chain/procurement/"
)

for entry in "${entities[@]}"; do
  read -r entity src_prefix ext dst_prefix <<< "$entry"
  echo "Processing $entity ($ext)"
  aws s3 ls "s3://$RAW_BUCKET/$src_prefix" --recursive | awk '{print $4}' | while read file; do
    if [[ "$file" == *$ext ]]; then
      fname=$(basename "$file")
      dest_key="$dst_prefix$fname"
      echo "Moving $file to $dest_key"
      aws s3 cp "s3://$RAW_BUCKET/$file" "s3://$STAGING_BUCKET/$dest_key"
      aws s3 rm "s3://$RAW_BUCKET/$file"
    fi
  done
done

# CRM interactions (JSON)
echo "Processing interactions (json)"
aws s3 ls "s3://$RAW_BUCKET/crm/interactions/interactions_2026/" --recursive | awk '{print $4}' | while read file; do
  if [[ "$file" == *.json ]]; then
    fname=$(basename "$file")
    dest_key="staging/crm/interactions/$fname"
    echo "Moving $file to $dest_key"
    aws s3 cp "s3://$RAW_BUCKET/$file" "s3://$STAGING_BUCKET/$dest_key"
    aws s3 rm "s3://$RAW_BUCKET/$file"
  fi
done

# IoT telemetry (JSON)
echo "Processing telemetry (json)"
aws s3 ls "s3://$RAW_BUCKET/iot/telemetry/telemetry_2026/" --recursive | awk '{print $4}' | while read file; do
  if [[ "$file" == *.json ]]; then
    fname=$(basename "$file")
    dest_key="staging/iot/telemetry/$fname"
    echo "Moving $file to $dest_key"
    aws s3 cp "s3://$RAW_BUCKET/$file" "s3://$STAGING_BUCKET/$dest_key"
    aws s3 rm "s3://$RAW_BUCKET/$file"
  fi
done

echo "Ingestion complete."
