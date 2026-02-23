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
            "speed": random.choice([random.randint(0,180),-50,9999]),
            "fuel_level": random.choice([random.randint(0,100),None,150]),
            "engine_temperature": random.choice([random.randint(70,110),200,-10]),
            "location_lat": round(random.uniform(-34.0,-22.0),4),
            "location_long": round(random.uniform(18.0,32.0),4)
        })
file = os.path.join(tmp_dir, "telemetry_2026.json")
with open(file, "w") as f:
    json.dump(telemetry, f, indent=2)
print(f"Uploading {file} to s3://{bucket}/iot/telemetry/telemetry_2026.json")
try:
    s3.upload_file(file, bucket, "iot/telemetry/telemetry_2026.json")
    print(f"Success: {file} uploaded to s3://{bucket}/iot/telemetry/telemetry_2026.json")
    os.remove(file)
    print(f"Local file {file} removed.")
except Exception as e:
    print(f"Error uploading {file} to S3: {e}")