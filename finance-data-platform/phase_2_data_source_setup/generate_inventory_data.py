import pandas as pd, boto3, random, os
from faker import Faker
from datetime import datetime, timedelta

fake = Faker()
s3 = boto3.client("s3")
bucket_name = "automotive-raw-data-lerato-2026"
tmp_dir = os.path.join(os.getcwd(), "tmp"); os.makedirs(tmp_dir, exist_ok=True)

start_date, end_date = datetime(2025,3,1), datetime(2026,2,28)
def random_date(): return start_date + timedelta(days=random.randint(0,(end_date-start_date).days))

def dirty_value(val,ch=0.1):
    if random.random()<ch: return None
    if random.random()<ch: return str(val)+"??"
    return val

def maybe_duplicate(df,ch=0.1):
    if random.random()<ch: return pd.concat([df,df.sample(1)],ignore_index=True)
    return df

inventory=[]
for i in range(200):
    inventory.append({
        "inventory_id": f"INV{i+1:03d}",
        "vehicle_id": f"VEH{random.randint(1,25):03d}",
        "dealer_id": f"DEAL{random.randint(1,15):03d}",
        "quantity": dirty_value(random.randint(0,10)),
        "stock_status": random.choice(["In Stock","Low Stock","Out of Stock"]),
        "last_updated": random_date()
    })
df=pd.DataFrame(inventory); df=maybe_duplicate(df,0.1)
file = os.path.join(tmp_dir, "inventory_2026.csv")
df.to_csv(file, index=False)
print(f"Uploading {file} to s3://{bucket_name}/inventory/vehicle_inventory/inventory_2026.csv")
try:
    s3.upload_file(file, bucket_name, "inventory/vehicle_inventory/inventory_2026.csv")
    print(f"Success: {file} uploaded to s3://{bucket_name}/inventory/vehicle_inventory/inventory_2026.csv")
    os.remove(file)
    print(f"Local file {file} removed.")
except Exception as e:
    print(f"Error uploading {file} to S3: {e}")