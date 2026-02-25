import pandas as pd, boto3, random, os, json
from faker import Faker
from datetime import datetime, timedelta

fake=Faker(); s3=boto3.client("s3")
bucket="automotive-raw-data-lerato-2026"
tmp_dir=os.path.join(os.getcwd(),"tmp"); os.makedirs(tmp_dir,exist_ok=True)

start,end=datetime(2025,3,1),datetime(2026,2,28)
def random_date(): return start+timedelta(days=random.randint(0,(end-start).days))

interactions=[]
for i in range(800):
    interactions.append({
        "interaction_id": f"INT{i+1:03d}",
        "customer_id": f"CUST{random.randint(1,250):03d}",
        "interaction_type": random.choice(["Inquiry","Complaint","Test Drive","Follow-up"]),
        "interaction_channel": random.choice(["Email","Phone","In-person","Website"]),
        "interaction_date": str(random_date()),
        "dealer_id": f"DEAL{random.randint(1,70):03d}",
        "employee_id": f"EMP{random.randint(1,50):03d}",
        "outcome": random.choice(["Interested","Not Interested","Purchased","No Response"]),
        "notes": fake.sentence() if random.random() > 0.2 else None
    })
df_interactions = pd.DataFrame(interactions)
file_json = os.path.join(tmp_dir, "interactions_2026.json")
with open(file_json, "w") as f:
    json.dump(interactions, f, indent=2)
print(f"Uploading {file_json} to s3://{bucket}/crm/interactions/interactions_2026/interactions_2026.json")
try:
    s3.upload_file(file_json, bucket, "crm/interactions/interactions_2026/interactions_2026.json")
    print(f"Success: {file_json} uploaded to s3://{bucket}/crm/interactions/interactions_2026/interactions_2026.json")
    os.remove(file_json)
    print(f"Local file {file_json} removed.")
    # Excel file
    file_xlsx = os.path.join(tmp_dir, "interactions_2026.xlsx")
    df_interactions.to_excel(file_xlsx, index=False)
    s3.upload_file(file_xlsx, bucket, "crm/interactions/interactions_2026/interactions_2026.xlsx")
    os.remove(file_xlsx)
    print(f"Uploaded interactions_2026.xlsx to S3.")
except Exception as e:
    print(f"Error uploading {file_json} to S3: {e}")