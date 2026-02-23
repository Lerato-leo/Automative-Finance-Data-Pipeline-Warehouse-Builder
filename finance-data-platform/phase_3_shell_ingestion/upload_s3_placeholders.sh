#!/bin/bash
# Upload .keep placeholder files to all key S3 prefixes to keep folders visible
BUCKETS=("automotive-raw-data-lerato-2026" "automotive-staging-data-lerato-2026" "automotive-archive-data-lerato-2026")
PREFIXES=(
  "crm/"
  "crm/interactions/"
  "erp/"
  "erp/customers/"
  "erp/dealers/"
  "erp/sales/"
  "erp/vehicles/"
  "finance/"
  "finance/payments/"
  "inventory/"
  "inventory/vehicle_inventory/"
  "iot/"
  "iot/telemetry/"
  "suppliers_chain/"
  "suppliers_chain/procurement/"
  "suppliers_chain/suppliers/"
)

for bucket in "${BUCKETS[@]}"; do
  for prefix in "${PREFIXES[@]}"; do
    echo "Uploading .keep to s3://$bucket/$prefix"
    echo "placeholder" | aws s3 cp - "s3://$bucket/$prefix.keep"
  done
done
