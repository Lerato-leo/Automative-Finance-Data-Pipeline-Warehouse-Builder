
import pandas as pd, boto3, random, os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
s3 = boto3.client("s3")
bucket = "automotive-raw-data-lerato-2026"
tmp_dir = os.path.join(os.getcwd(), "tmp")
os.makedirs(tmp_dir, exist_ok=True)

start, end = datetime(2025, 3, 1), datetime(2026, 2, 28)
def random_date():
    return start + timedelta(days=random.randint(0, (end - start).days))

def upload_file_with_error_handling(local_path, bucket, s3_key):
    print(f"Uploading {local_path} to s3://{bucket}/{s3_key}")
    try:
        s3.upload_file(local_path, bucket, s3_key)
        print(f"Success: {local_path} uploaded to s3://{bucket}/{s3_key}")
        os.remove(local_path)
        print(f"Local file {local_path} removed.")
    except Exception as e:
        print(f"Error uploading {local_path} to S3: {e}")

suppliers = []
for i in range(30):
    suppliers.append({
        "supplier_id": f"SUP{i+1:03d}",
        "supplier_name": fake.company() if random.random() > 0.2 else fake.company() + "??",
        "country": "South Africa",
        "contact_email": fake.company_email() if random.random() > 0.2 else "not-an-email",
        "supplier_type": random.choice(["Manufacturer", "Parts Supplier"]),
        "status": random.choice(["Active", "Inactive"])
    })
df_sup = pd.DataFrame(suppliers)
file1 = os.path.join(tmp_dir, "suppliers_2026.csv")
df_sup.to_csv(file1, index=False)
upload_file_with_error_handling(file1, bucket, "suppliers_chain/suppliers/suppliers_2026/suppliers_2026.csv")
file1_xlsx = os.path.join(tmp_dir, "suppliers_2026.xlsx")
df_sup.to_excel(file1_xlsx, index=False)
upload_file_with_error_handling(file1_xlsx, bucket, "suppliers_chain/suppliers/suppliers_2026/suppliers_2026.xlsx")

proc = []
for i in range(200):
    proc.append({
        "procurement_id": f"PROC{i+1:03d}",
        "supplier_id": f"SUP{random.randint(1,30):03d}",
        "vehicle_id": f"VEH{random.randint(1,45):03d}",
        "cost_price": random.randint(200000,500000) if random.random() > 0.2 else random.choice([-10000, 99999999]),
        "procurement_date": str(random_date()),
        "status": random.choice(["Ordered", "Delivered", "Cancelled"])
    })
df_proc = pd.DataFrame(proc)
file2 = os.path.join(tmp_dir, "procurement_2026.csv")
df_proc.to_csv(file2, index=False)
upload_file_with_error_handling(file2, bucket, "suppliers_chain/procurement/procurement_2026/procurement_2026.csv")
file2_xlsx = os.path.join(tmp_dir, "procurement_2026.xlsx")
df_proc.to_excel(file2_xlsx, index=False)
upload_file_with_error_handling(file2_xlsx, bucket, "suppliers_chain/procurement/procurement_2026/procurement_2026.xlsx")