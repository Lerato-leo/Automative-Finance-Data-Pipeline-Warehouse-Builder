import boto3
import os

RAW_BUCKET = "automotive-raw-data-lerato-2026"
STAGING_BUCKET = "automotive-staging-data-lerato-2026"
s3 = boto3.client("s3")

entities = {
    'customers': ('erp/customers/customers_2026/', '.xlsx', 'staging/erp/customers/'),
    'dealers': ('erp/dealers/dealers_2026/', '.xlsx', 'staging/erp/dealers/'),
    'sales': ('erp/sales/sales_2026/', '.csv', 'staging/erp/sales/'),
    'vehicles': ('erp/vehicles/vehicles_2026/', '.csv', 'staging/erp/vehicles/'),
    'inventory': ('erp/inventory/inventory_2026/', '.csv', 'staging/erp/inventory/'),
    'payments': ('finance/payments/payments_2026/', '.csv', 'staging/finance/payments/'),
    'suppliers': ('suppliers_chain/suppliers/suppliers_2026/', '.csv', 'staging/suppliers_chain/suppliers/'),
    'procurement': ('suppliers_chain/procurement/procurement_2026/', '.csv', 'staging/suppliers_chain/procurement/'),
}

for entity, (src_prefix, ext, dst_prefix) in entities.items():
    response = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix=src_prefix)
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(ext):
            filename = os.path.basename(key)
            dest_key = dst_prefix + filename
            s3.copy_object(Bucket=STAGING_BUCKET, CopySource={'Bucket': RAW_BUCKET, 'Key': key}, Key=dest_key)
            s3.delete_object(Bucket=RAW_BUCKET, Key=key)
            print(f"Moved {key} to {dest_key}")

# CRM interactions (JSON)
response = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix='crm/interactions/interactions_2026/')
for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith('.json'):
        filename = os.path.basename(key)
        dest_key = 'staging/crm/interactions/' + filename
        s3.copy_object(Bucket=STAGING_BUCKET, CopySource={'Bucket': RAW_BUCKET, 'Key': key}, Key=dest_key)
        s3.delete_object(Bucket=RAW_BUCKET, Key=key)
        print(f"Moved {key} to {dest_key}")

# IoT telemetry (JSON)
response = s3.list_objects_v2(Bucket=RAW_BUCKET, Prefix='iot/telemetry/telemetry_2026/')
for obj in response.get('Contents', []):
    key = obj['Key']
    if key.endswith('.json'):
        filename = os.path.basename(key)
        dest_key = 'staging/iot/telemetry/' + filename
        s3.copy_object(Bucket=STAGING_BUCKET, CopySource={'Bucket': RAW_BUCKET, 'Key': key}, Key=dest_key)
        s3.delete_object(Bucket=RAW_BUCKET, Key=key)
        print(f"Moved {key} to {dest_key}")

print("Ingestion complete.")
