import boto3, json
BUCKET = 'automotive-staging-data-lerato-2026'
KEY = 'path/to/file.json'  # Replace with actual S3 key
LOCAL_FILE = '/tmp/file.json'
s3 = boto3.client('s3')
s3.download_file(BUCKET, KEY, LOCAL_FILE)
with open(LOCAL_FILE) as f:
    data = json.load(f)
# Transform data as needed
# Example: print first record
print(data[0])
# Optionally: load to Postgres or S3
