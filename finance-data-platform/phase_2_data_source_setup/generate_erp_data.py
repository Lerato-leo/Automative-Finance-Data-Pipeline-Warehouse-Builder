import pandas as pd
import boto3
import random
from faker import Faker
from datetime import datetime, timedelta
import os
import tempfile

# Setup Faker with default locale (for compatibility)
fake = Faker()

tmp_dir = tempfile.gettempdir()
# Setup S3 client
s3 = boto3.client("s3")
bucket_name = "automotive-raw-data-lerato-2026"

start_date = datetime(2025, 3, 1)
end_date = datetime(2026, 2, 28)
def random_date():
    return start_date + timedelta(days=random.randint(0, (end_date - start_date).days))
def dirty_value(value, chance=0.1):
    if random.random() < chance:
        return None
    if random.random() < chance:
        return str(value) + "??"
    return value
def dirty_vehicle_vin(vin, chance=0.15):
    r = random.random()
    if r < chance/3:
        return None
    elif r < 2*chance/3:
        return vin + "X" * random.randint(1, 3)
    elif r < chance:
        return vin[:5]
    return vin
def dirty_price(price, chance=0.1):
    r = random.random()
    if r < chance/2:
        return -abs(price)
    elif r < chance:
        return price * 100
    return price
def dirty_date(date, chance=0.1):
    if random.random() < chance:
        return "31-02-2025"
    return date
def dirty_email(email, chance=0.1):
    if random.random() < chance:
        return "not-an-email"
    return email

# Generate customers
customers = []
for i in range(250):
    customers.append({
        "customer_id": f"CUST{i+1:03d}",
        "first_name": fake.first_name(),
        "last_name": fake.last_name(),
        "email": dirty_email(fake.email(), 0.1),
        "created_at": random_date()
    })
df_customers = pd.DataFrame(customers)
file_cust = "customers_2026.csv"
df_customers.to_csv(file_cust, index=False)
s3.upload_file(file_cust, bucket_name, "erp/customers/customers_2026.csv")
os.remove(file_cust)

# Generate dealers
dealers = []
for i in range(70):
    dealers.append({
        "dealer_id": f"DEAL{i+1:03d}",
        "dealer_name": fake.company(),
        "location": fake.city(),
        "contact_email": dirty_email(fake.company_email(), 0.1),
        "created_at": random_date()
    })
df_dealers = pd.DataFrame(dealers)
file_deal = "dealers_2026.csv"
df_dealers.to_csv(file_deal, index=False)
s3.upload_file(file_deal, bucket_name, "erp/dealers/dealers_2026.csv")
os.remove(file_deal)

# Generate vehicles
vehicles = []
for i in range(45):
    vehicles.append({
        "vehicle_id": f"VEH{i+1:03d}",
        "model": fake.word().capitalize(),
        "dealer_id": f"DEAL{random.randint(1,70):03d}",
        "year": random.randint(2015,2026),
        "vin": dirty_vehicle_vin(fake.bothify(text='??#####??'), 0.15)
    })
df_vehicles = pd.DataFrame(vehicles)
file_veh = "vehicles_2026.csv"
df_vehicles.to_csv(file_veh, index=False)
s3.upload_file(file_veh, bucket_name, "erp/vehicles/vehicles_2026.csv")
os.remove(file_veh)

# Generate sales
sales = []
for i in range(1500):
    sales.append({
        "sale_id": f"SALE{i+1:04d}",
        "customer_id": f"CUST{random.randint(1,250):03d}",
        "vehicle_id": f"VEH{random.randint(1,45):03d}",
        "sale_price": dirty_price(random.randint(10000,50000), 0.1),
        "sale_date": dirty_date(random_date(), 0.1),
        "dealer_id": f"DEAL{random.randint(1,70):03d}",
        "created_at": random_date()
    })
df_sales = pd.DataFrame(sales)
file_sales = "sales_2026.csv"
df_sales.to_csv(file_sales, index=False)
s3.upload_file(file_sales, bucket_name, "erp/sales/sales_2026.csv")
os.remove(file_sales)

def maybe_duplicate(df, chance=0.1):
    if random.random() < chance:
        return pd.concat([df, df.sample(1)], ignore_index=True)
    return df

# -----------------------------
# Generate Customers (100 rows)
# -----------------------------

# Generate Customers (100 rows) with dirty data and possible duplicates
customers = []
for i in range(100):
    customers.append({
        "customer_id": f"CUST{i+1:03d}",
        "first_name": dirty_value(fake.first_name()),
        "last_name": fake.last_name(),
        "email": dirty_email(fake.email()),
        "phone": dirty_value(fake.phone_number()),
        "date_of_birth": dirty_value(fake.date_of_birth(minimum_age=18, maximum_age=70)),
        "gender": random.choice(["Male","Female","Other","Unknown"]),
        "street_number": random.randint(1, 999),
        "street_name": fake.street_name(),
        "suburb": fake.city(),
        "city": fake.city(),
        "province": random.choice([
            "Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape",
            "Free State","Limpopo","Mpumalanga","North West","Northern Cape"
        ]),
        "postal_code": fake.postcode(),
        "country": "South Africa",
        "created_at": random_date(),
        "status": random.choice(["Active","Inactive","Suspended"])
    })
df_customers = pd.DataFrame(customers)
df_customers = maybe_duplicate(df_customers, 0.1)
customer_file = os.path.join(tmp_dir, "customers_2026.xlsx")
df_customers.to_excel(customer_file, index=False)
s3.upload_file(customer_file, bucket_name, "erp/customers/customers_2026.xlsx")
os.remove(customer_file)
print("Uploaded customers_2026.xlsx to S3.")

# -----------------------------
# Generate Vehicles (25 models)
# -----------------------------

# Generate Vehicles (25 models) with dirty VINs and possible duplicates
vehicles = []
brands = ["Toyota","Ford","BMW","Volkswagen","Mercedes-Benz","Audi"]
for i in range(25):
    vin = f"VIN{random.randint(1000000000,9999999999)}"
    vehicles.append({
        "vehicle_id": f"VEH{i+1:03d}",
        "vin": dirty_vehicle_vin(vin),
        "make": random.choice(brands),
        "model": fake.word().capitalize(),
        "year": random.choice([2025,2026,-2025]),  # possible negative year
        "color": random.choice(["White","Black","Silver","Blue","Red"]),
        "engine_type": random.choice(["Petrol","Diesel","Hybrid","Electric"]),
        "transmission": random.choice(["Manual","Automatic"]),
        "manufacture_country": random.choice(["South Africa","Japan","Germany"]),
        "manufacture_date": dirty_date(random_date().date()),
        "status": random.choice(["Available","Sold","Maintenance","Retired"]),
        "created_at": random_date()
    })
df_vehicles = pd.DataFrame(vehicles)
df_vehicles = maybe_duplicate(df_vehicles, 0.1)
vehicle_file = os.path.join(tmp_dir, "vehicles_2026.csv")
df_vehicles.to_csv(vehicle_file, index=False)
s3.upload_file(vehicle_file, bucket_name, "erp/vehicles/vehicles_2026.csv")
os.remove(vehicle_file)
print("Uploaded vehicles_2026.csv to S3.")

# -----------------------------
# Generate Dealers (15 rows)
# -----------------------------
def maybe_duplicate(df, chance=0.1):
    if random.random() < chance:
        return pd.concat([df, df.sample(1)], ignore_index=True)
    return df
    dealers.append({
        "dealer_id": f"DEAL{i+1:03d}",
        "dealer_name": fake.company(),
        "dealer_code": f"DC{i+1:03d}",
        "street_number": random.randint(1, 999),
        "street_name": fake.street_name(),
        "city": fake.city(),
        "province": random.choice([
            "Gauteng","Western Cape","KwaZulu-Natal","Eastern Cape",
            "Free State","Limpopo","Mpumalanga","North West","Northern Cape"
        ]),
        "postal_code": fake.postcode(),
        "country": "South Africa",
        "phone": dirty_value(fake.phone_number()),
        "email": dirty_email(fake.company_email()),
        "dealer_type": random.choice(["Franchise","Independent"]),
        "status": random.choice(["Active","Inactive"]),
        "created_at": random_date()
    })
df_dealers = pd.DataFrame(dealers)
df_dealers = maybe_duplicate(df_dealers, 0.1)
dealer_file = os.path.join(tmp_dir, "dealers_2026.xlsx")
df_dealers.to_excel(dealer_file, index=False)
s3.upload_file(dealer_file, bucket_name, "erp/dealers/dealers_2026.xlsx")
os.remove(dealer_file)
print("Uploaded dealers_2026.xlsx to S3.")

# -----------------------------
# Generate Sales (~500 rows)
# -----------------------------

# Generate Sales (~500 rows) with dirty prices, dates, and possible duplicates
sales = []
for i in range(500):
    sale_price = random.randint(200000, 800000)
    discount = random.choice([0,5000,10000,20000])
    sales.append({
        "sale_id": f"SALE{i+1:04d}",
        "sale_date": dirty_date(random_date().date()),
        "customer_id": random.choice(df_customers["customer_id"]),
        "vehicle_id": random.choice(df_vehicles["vehicle_id"]),
        "dealer_id": random.choice(df_dealers["dealer_id"]),
        "sale_price": dirty_price(sale_price),
        "discount_amount": discount,
        "final_price": lambda sp, da: sp - da,
        "sale_channel": random.choice(["Dealer","Online","Fleet"]),
        "sale_status": random.choice(["Completed","Cancelled","Pending"]),
        "created_at": random_date()
    })
df_sales = pd.DataFrame(sales)
# Fix final_price calculation
df_sales["final_price"] = df_sales["sale_price"] - df_sales["discount_amount"]
df_sales = maybe_duplicate(df_sales, 0.1)
sales_file = os.path.join(tmp_dir, "sales_2026.csv")
df_sales.to_csv(sales_file, index=False)
s3.upload_file(sales_file, bucket_name, "erp/sales/sales_2026.csv")
os.remove(sales_file)
print("Uploaded sales_2026.csv to S3.")

# Generate Inventory (now part of ERP)
inventory = []
for i in range(500):
    inventory.append({
        "inventory_id": f"INV{i+1:04d}",
        "vehicle_id": f"VEH{random.randint(1,45):03d}",
        "dealer_id": random.choice(df_dealers["dealer_id"]),
        "quantity": random.randint(1, 100),
        "stock_status": random.choice(["InStock","OutOfStock","Reserved"]),
        "last_updated": random_date()
    })
df_inventory = pd.DataFrame(inventory)
inventory_file = os.path.join(tmp_dir, "inventory_2026.csv")
df_inventory.to_csv(inventory_file, index=False)
s3.upload_file(inventory_file, bucket_name, "erp/inventory/inventory_2026/inventory_2026.csv")
os.remove(inventory_file)
print("Uploaded inventory_2026.csv to S3.")

print("ERP data (customers, vehicles, dealers, sales, inventory) uploaded to S3 successfully!")