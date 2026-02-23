import pandas as pd, boto3, random, os, json
from faker import Faker
from datetime import datetime, timedelta

fake=Faker(); s3=boto3.client("s3")
bucket="automotive-raw-data-lerato-2026"
tmp_dir=os.path.join(os.getcwd(),"tmp"); os.makedirs(tmp_dir,exist_ok=True)

start,end=datetime(2025,3,1),datetime(2026,2,28)
def random_date(): return start+timedelta(days=random.randint(0,(end-start).days))

interactions=[]
for i in range(350):
    interactions.append({
        "interaction_id": f"INT{i+1:03d}",
        "customer_id": f"CUST{random.randint(1,100):03d}",
        "interaction_type": random.choice(["Inquiry","Complaint","Test Drive","Follow-up"]),
        "interaction_channel": random.choice(["Email","Phone","In-person","Website"]),
        "interaction_date": str(random_date()),
        "dealer_id": f"DEAL{random.randint(1,15):03d}",
        "employee_id": f"EMP{random.randint(1,50):03d}",
        "outcome": random.choice(["Interested","Not Interested","Purchased","No Response"]),
        "notes": random.choice([fake.sentence(),None,""])
    })
file = os.path.join(tmp_dir, "interactions_2026.json")
with open(file, "w") as f:
    json.dump(interactions, f, indent=2)
print(f"Uploading {file} to s3://{bucket}/crm/interactions/interactions_2026.json")
try:
    s3.upload_file(file, bucket, "crm/interactions/interactions_2026.json")
    print(f"Success: {file} uploaded to s3://{bucket}/crm/interactions/interactions_2026.json")
    os.remove(file)
    print(f"Local file {file} removed.")
except Exception as e:
    print(f"Error uploading {file} to S3: {e}")