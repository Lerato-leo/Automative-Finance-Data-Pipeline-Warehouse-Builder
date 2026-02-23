import boto3, pandas as pd, psycopg2
import os
BUCKET = 'automotive-staging-data-lerato-2026'
KEY = 'path/to/file.csv'  # Replace with actual S3 key
LOCAL_FILE = '/tmp/file.csv'
s3 = boto3.client('s3')
s3.download_file(BUCKET, KEY, LOCAL_FILE)
df = pd.read_csv(LOCAL_FILE)
conn = psycopg2.connect("dbname=yourdb user=youruser password=yourpass host=yourhost")
df.to_sql('staging_table', conn, if_exists='append', index=False)
os.remove(LOCAL_FILE)
print('CSV loaded to Postgres.')
