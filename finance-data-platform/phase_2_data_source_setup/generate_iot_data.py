import pandas as pd
import boto3, random, os, json
from datetime import datetime, timedelta

s3=boto3.client("s3"); bucket="automotive-raw-data-lerato-2026"
tmp_dir=os.path.join(os.getcwd(),"tmp"); os.makedirs(tmp_dir,exist_ok=True)

start,end=datetime(2025,3,1),datetime(2026,2,28)
def random_date(): return start+timedelta(days=random.randint(0,(end-start).days))

telemetry=[]
for v in range(1,11):  # 10 vehicles tracked
    for i in range(random.randint(50,100)):
        telemetry.append({
            "telemetry_id": f"TEL{v:02d}{i+1:03d}",
            "vehicle_id": f"VEH{v:03d}",
            "timestamp": str(random_date()),
            "speed": random.randint(0,180) if random.random() > 0.2 else random.choice([-50,9999]),
            "fuel_level": random.randint(0,100) if random.random() > 0.2 else None,
            "engine_temperature": random.randint(70,110) if random.random() > 0.2 else random.choice([200,-10]),
            "location_lat": round(random.uniform(-34.0,-22.0),4),
            "location_long": round(random.uniform(18.0,32.0),4)
        })
df_telemetry = pd.DataFrame(telemetry)
file_json = os.path.join(tmp_dir, "telemetry_2026.json")
with open(file_json, "w") as f:
    json.dump(telemetry, f, indent=2)
print(f"Uploading {file_json} to s3://{bucket}/iot/telemetry/telemetry_2026/telemetry_2026.json")
try:
    s3.upload_file(file_json, bucket, "iot/telemetry/telemetry_2026/telemetry_2026.json")
    print(f"Success: {file_json} uploaded to s3://{bucket}/iot/telemetry/telemetry_2026/telemetry_2026.json")
    os.remove(file_json)
    print(f"Local file {file_json} removed.")
    # Excel file
    file_xlsx = os.path.join(tmp_dir, "telemetry_2026.xlsx")
    df_telemetry.to_excel(file_xlsx, index=False)
    s3.upload_file(file_xlsx, bucket, "iot/telemetry/telemetry_2026/telemetry_2026.xlsx")
    os.remove(file_xlsx)
    print(f"Uploaded telemetry_2026.xlsx to S3.")
except Exception as e:
    print(f"Error uploading {file_json} to S3: {e}")