import pandas as pd, boto3, random, os
from datetime import datetime, timedelta

s3=boto3.client("s3"); bucket="automotive-raw-data-lerato-2026"
tmp_dir=os.path.join(os.getcwd(),"tmp"); os.makedirs(tmp_dir,exist_ok=True)

start,end=datetime(2025,3,1),datetime(2026,2,28)
def random_date(): return start+timedelta(days=random.randint(0,(end-start).days))

payments=[]
for i in range(500):
    payments.append({
        "payment_id": f"PAY{i+1:04d}",
        "sale_id": f"SALE{random.randint(1,500):04d}",
        "payment_date": str(random_date()),
        "payment_amount": random.choice([random.randint(200000,800000),-5000,99999999]),
        "payment_method": random.choice(["Cash","Credit Card","Bank Transfer","Financing"]),
        "payment_status": random.choice(["Completed","Failed","Pending"]),
        "transaction_reference": f"TXN{random.randint(100000,999999)}",
        "created_at": random_date()
    })
df=pd.DataFrame(payments)
file = os.path.join(tmp_dir, "payments_2026.csv")
df.to_csv(file, index=False)
print(f"Uploading {file} to s3://{bucket}/finance/payments/payments_2026.csv")
try:
    s3.upload_file(file, bucket, "finance/payments/payments_2026.csv")
    print(f"Success: {file} uploaded to s3://{bucket}/finance/payments/payments_2026.csv")
    os.remove(file)
    print(f"Local file {file} removed.")
except Exception as e:
    print(f"Error uploading {file} to S3: {e}")