import boto3, pandas as pd
BUCKET = 'automotive-staging-data-lerato-2026'
KEY = 'path/to/file.xlsx'  # Replace with actual S3 key
LOCAL_FILE = '/tmp/file.xlsx'
s3 = boto3.client('s3')
s3.download_file(BUCKET, KEY, LOCAL_FILE)
df = pd.read_excel(LOCAL_FILE)
print(df.head())
# Optionally: load to Postgres or S3
