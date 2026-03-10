"""Phase 4 ETL pipeline with integrated logging and data-quality validation."""

from __future__ import annotations

import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from time import perf_counter

import boto3
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from phase_8_monitoring_logging.logging.logging_config import configure_pipeline_logger, log_quality_metrics


# ----------------------------
# ENV LOADER
# ----------------------------
def load_env_file(env_path):
    env_file = Path(__file__).parent / env_path
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if line.strip() and not line.strip().startswith('#'):
                    k, v = line.strip().split('=', 1)
                    os.environ[k] = v.strip().strip('"')


load_env_file('warehouse_conn.env')

LOGGER = configure_pipeline_logger("phase_4_python_etl")


# ----------------------------
# CONFIG
# ----------------------------
STAGING_BUCKET = os.getenv('STAGING_BUCKET', 'automotive-staging-data-lerato-2026')
WAREHOUSE_CONN = os.getenv(
    'WAREHOUSE_CONN',
    'dbname=yourdb user=youruser password=yourpass host=yourhost'
)
INCREMENTAL = os.getenv('INCREMENTAL', 'false').lower() == 'true'
CURRENT_RUN_STAGING_KEYS = os.getenv('CURRENT_RUN_STAGING_KEYS', '')

s3 = boto3.client('s3')

QUALITY_RULES = {
    'stg_customers': {'required_columns': ['customer_id', 'email'], 'critical_columns': ['customer_id']},
    'stg_dealers': {'required_columns': ['dealer_id'], 'critical_columns': ['dealer_id']},
    'stg_vehicles': {'required_columns': ['vehicle_id', 'dealer_id'], 'critical_columns': ['vehicle_id']},
    'stg_sales': {'required_columns': ['sale_id', 'sale_date'], 'critical_columns': ['sale_id', 'sale_date']},
    'stg_inventory': {'required_columns': ['inventory_id', 'vehicle_id'], 'critical_columns': ['inventory_id']},
    'stg_payments': {'required_columns': ['payment_id', 'payment_date'], 'critical_columns': ['payment_id', 'payment_date']},
    'stg_suppliers': {'required_columns': ['supplier_id'], 'critical_columns': ['supplier_id']},
    'stg_procurement': {'required_columns': ['procurement_id', 'supplier_id'], 'critical_columns': ['procurement_id', 'supplier_id']},
    'stg_interactions': {'required_columns': ['interaction_id', 'customer_id'], 'critical_columns': ['interaction_id', 'customer_id']},
    'stg_telemetry': {'required_columns': ['telemetry_id', 'timestamp'], 'critical_columns': ['telemetry_id', 'timestamp']},
}


def detect_file_type(key):
    extension_map = {
        '.csv': 'CSV',
        '.json': 'JSON',
        '.xlsx': 'Excel',
    }
    return extension_map.get(Path(key).suffix.lower(), 'Unknown')


# ----------------------------
# TABLE MAP
# ----------------------------
TABLE_MAP = {
    'stg_customers': 'staging_customers',
    'stg_dealers': 'staging_dealers',
    'stg_vehicles': 'staging_vehicles',
    'stg_sales': 'staging_sales',
    'stg_inventory': 'staging_inventory',
    'stg_payments': 'staging_payments',
    'stg_suppliers': 'staging_suppliers',
    'stg_procurement': 'staging_procurement',
    'stg_interactions': 'staging_interactions',
    'stg_telemetry': 'staging_telemetry',
}

TABLE_ALIASES = {
    'stg_interactions': ('customer_interactions', 'interaction'),
    'stg_customers': ('crm_customers', 'customer'),
    'stg_dealers': ('dealer',),
    'stg_vehicles': ('vehicle',),
    'stg_sales': ('sales',),
    'stg_inventory': ('inventory',),
    'stg_payments': ('payment', 'erp_finance'),
    'stg_suppliers': ('supplier',),
    'stg_procurement': ('procurement', 'purchase_order', 'purchase_orders', 'order'),
    'stg_telemetry': ('telemetry', 'sensor', 'iot_sensors'),
}


# ----------------------------
# FILE DISCOVERY
# ----------------------------
def parse_current_run_staging_keys():
    if not CURRENT_RUN_STAGING_KEYS:
        return []

    try:
        parsed = json.loads(CURRENT_RUN_STAGING_KEYS)
    except json.JSONDecodeError:
        LOGGER.warning('CURRENT_RUN_STAGING_KEYS is not valid JSON. Falling back to full staging scan.')
        return []

    if not isinstance(parsed, list):
        LOGGER.warning('CURRENT_RUN_STAGING_KEYS must be a list. Falling back to full staging scan.')
        return []

    return [key for key in parsed if isinstance(key, str) and key.endswith(('.csv', '.json', '.xlsx'))]


def list_staging_files():
    current_run_keys = parse_current_run_staging_keys()
    if current_run_keys:
        LOGGER.info("Using %s staged file(s) from the current DAG run.", len(current_run_keys))
        return current_run_keys

    paginator = s3.get_paginator('list_objects_v2')
    files = []

    for page in paginator.paginate(Bucket=STAGING_BUCKET):
        files.extend([obj['Key'] for obj in page.get('Contents', [])])

    valid = [f for f in files if f.endswith(('.csv', '.json', '.xlsx'))]

    LOGGER.info("Found %s valid staging file(s).", len(valid))
    return valid


# ----------------------------
# EXTRACT
# ----------------------------
def extract_file(key):
    obj = s3.get_object(Bucket=STAGING_BUCKET, Key=key)

    if key.endswith('.csv'):
        return pd.read_csv(obj['Body'])

    if key.endswith('.json'):
        return pd.json_normalize(json.load(obj['Body']))

    if key.endswith('.xlsx'):
        return pd.read_excel(BytesIO(obj['Body'].read()))

    raise ValueError(f"Unsupported file format: {key}")


def normalize_column_aliases(df, table_key):
    column_aliases = {
        'stg_customers': {
            'created_date': 'created_at',
            'zip': 'zip_code',
        },
        'stg_interactions': {
            'type': 'interaction_type',
            'timestamp': 'interaction_date',
            'created_date': 'interaction_date',
            'subject': 'notes',
        },
        'stg_payments': {
            'transaction_id': 'payment_id',
            'transaction_date': 'payment_date',
            'payment_amount': 'amount',
            'payment_status': 'status',
        },
        'stg_suppliers': {
            'contact_person': 'contact_name',
            'email': 'contact_email',
            'phone': 'contact_phone',
            'zip': 'zip_code',
            'created_date': 'created_at',
        },
        'stg_procurement': {
            'po_id': 'procurement_id',
            'vendor_id': 'supplier_id',
            'po_date': 'procurement_date',
            'amount': 'cost',
            'procurement_status': 'status',
        },
        'stg_telemetry': {
            'device_id': 'telemetry_id',
            'reading_type': 'sensor_type',
            'reading_value': 'sensor_value',
        },
    }

    aliases = column_aliases.get(table_key, {})
    if not aliases:
        return df

    rename_map = {}
    for source_name, target_name in aliases.items():
        if source_name in df.columns and target_name not in df.columns:
            rename_map[source_name] = target_name

    if rename_map:
        df = df.rename(columns=rename_map)

    if table_key == 'stg_customers' and 'name' in df.columns:
        if 'first_name' not in df.columns:
            df['first_name'] = df['name'].astype(str).str.split().str[0]
        if 'last_name' not in df.columns:
            df['last_name'] = df['name'].astype(str).str.split().str[1:].str.join(' ')

    if table_key == 'stg_payments' and 'status' in df.columns:
        payment_status_map = {
            'completed': 'Paid',
            'paid': 'Paid',
            'pending': 'Pending',
            'failed': 'Failed',
            'cancelled': 'Failed',
            'canceled': 'Failed',
            'refunded': 'Refunded',
        }
        normalized = df['status'].astype(str).str.strip().str.lower().map(payment_status_map)
        df['status'] = normalized.fillna(df['status'])

    if table_key == 'stg_procurement' and 'status' in df.columns:
        procurement_status_map = {
            'ordered': 'Ordered',
            'received': 'Received',
            'returned': 'Returned',
            'pending': 'Ordered',
            'completed': 'Received',
        }
        normalized = df['status'].astype(str).str.strip().str.lower().map(procurement_status_map)
        df['status'] = normalized.fillna(df['status'])

    return df


# ----------------------------
# TRANSFORM
# ----------------------------
def transform(df, table_key):
    df = df.drop_duplicates()
    df = df.dropna(how='all')
    df = normalize_column_aliases(df, table_key)

    # Trim whitespace
    for col in df.select_dtypes(include='string').columns:
        df[col] = df[col].astype(str).str.strip()

    # Normalize email
    if 'email' in df.columns:
        df['email'] = df['email'].str.lower()
        df = df[df['email'].str.contains('@', na=False)]

    if 'date_of_birth' in df.columns:
        df['date_of_birth'] = pd.to_datetime(df['date_of_birth'], errors='coerce')

    if 'sale_date' in df.columns:
        df['sale_date'] = pd.to_datetime(df['sale_date'], errors='coerce')

    # Numeric clean
    for col in df.columns:
        if 'price' in col or 'amount' in col:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Add is_dirty flag for tracking data quality issues
    if 'is_dirty' not in df.columns:
        df['is_dirty'] = False

    # Categorical field validation - 16 business rule constraints
    categorical_rules = {
        'gender': ['M', 'F', 'Other'],
        'status': ['Active', 'Inactive', 'Pending', 'Closed'],
        'province': ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'NT', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
        'engine_type': ['Gasoline', 'Diesel', 'Electric', 'Hybrid', 'Plug-in Hybrid'],
        'transmission': ['Manual', 'Automatic', 'CVT'],
        'vehicle_status': ['Available', 'Sold', 'Reserved', 'Damaged'],
        'sale_channel': ['Dealership', 'Online', 'Auction', 'Private'],
        'sale_status': ['Completed', 'Pending', 'Cancelled'],
        'stock_status': ['In Stock', 'Out of Stock', 'Coming Soon'],
        'interaction_type': ['Phone', 'Email', 'Chat', 'In-Person'],
        'interaction_channel': ['Sales', 'Support', 'Marketing'],
        'outcome': ['Won', 'Lost', 'Pending', 'Cancelled'],
        'payment_method': ['Credit Card', 'Debit Card', 'Check', 'Bank Transfer'],
        'payment_status': ['Paid', 'Pending', 'Failed', 'Refunded'],
        'procurement_status': ['Ordered', 'Received', 'Returned'],
    }

    if table_key == 'stg_payments':
        categorical_rules['status'] = ['Paid', 'Pending', 'Failed', 'Refunded']
    elif table_key == 'stg_procurement':
        categorical_rules['status'] = ['Ordered', 'Received', 'Returned']

    for col, allowed_values in categorical_rules.items():
        if col in df.columns:
            invalid_rows = ~df[col].isin(allowed_values)
            if invalid_rows.any():
                df.loc[invalid_rows, 'is_dirty'] = True

    return df


def evaluate_data_quality(df, table_key, target_columns):
    rules = QUALITY_RULES.get(table_key, {'required_columns': [], 'critical_columns': []})
    duplicate_records = int(df.duplicated().sum())
    null_value_counts = {column: int(df[column].isna().sum()) for column in df.columns}
    total_null_values = int(sum(null_value_counts.values()))
    required_columns = rules['required_columns']
    missing_required_columns = [column for column in required_columns if column not in df.columns]
    critical_null_violations = {
        column: null_value_counts[column]
        for column in rules['critical_columns']
        if column in null_value_counts and null_value_counts[column] > 0
    }
    shared_columns = sorted(set(df.columns) & set(target_columns))
    unexpected_columns = sorted(set(df.columns) - set(target_columns))
    schema_validation = {
        'shared_columns': len(shared_columns),
        'missing_required_columns': missing_required_columns,
        'unexpected_columns': unexpected_columns,
        'is_valid': bool(shared_columns) and not missing_required_columns,
    }

    validation_errors = []
    if duplicate_records > 0:
        validation_errors.append(f'duplicate records detected: {duplicate_records}')
    if missing_required_columns:
        validation_errors.append(f'missing required columns: {missing_required_columns}')
    if critical_null_violations:
        validation_errors.append(f'critical null violations: {critical_null_violations}')
    if not schema_validation['is_valid'] and not missing_required_columns:
        validation_errors.append('schema validation failed because no target columns matched the extracted file')

    return {
        'row_count': int(len(df)),
        'total_null_values': total_null_values,
        'null_value_counts': null_value_counts,
        'duplicate_records': duplicate_records,
        'schema_validation': schema_validation,
        'validation_errors': validation_errors,
    }


# ----------------------------
# GET TABLE COLUMNS
# ----------------------------
def get_table_columns(conn, table_name):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = 'staging'
            AND table_name = %s
        """, (table_name,))
        return [row[0] for row in cur.fetchall()]


# ----------------------------
# UPSERT
# ----------------------------
def upsert(df, table_key, conn):

    table_name = TABLE_MAP[table_key]
    target_table = f"staging.{table_name}"

    # Filter out dirty records (data quality issues)
    if 'is_dirty' in df.columns:
        clean_df = df[df['is_dirty'] == False].copy()
        dirty_count = len(df) - len(clean_df)
        if dirty_count > 0:
            LOGGER.info("Filtered %s dirty record(s) from staging.%s", dirty_count, table_name)
        df = clean_df

    # Get table columns from database
    table_columns = get_table_columns(conn, table_name)

    # Keep only matching columns
    df = df[[c for c in df.columns if c in table_columns]]

    if df.empty:
        LOGGER.info("No matching columns remained after target-table alignment for staging.%s", table_name)
        return 0

    cols = list(df.columns)
    column_str = ",".join(cols)

    # Convert dataframe to list of tuples (fast)
    # Replace NaN / NaT with None for PostgreSQL
    values = [tuple(None if pd.isna(x) else x for x in row) for row in df.to_numpy()]

    sql = f"""
        INSERT INTO {target_table} ({column_str})
        VALUES %s
        ON CONFLICT DO NOTHING
    """

    with conn.cursor() as cur:
        execute_values(
            cur,
            sql,
            values,
            page_size=1000
        )

    conn.commit()

    return len(values)


# ----------------------------
# METADATA UPDATE
# ----------------------------
def update_metadata(table_key, row_count, conn):

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO staging.etl_metadata
            (table_name, load_time, row_count)
            VALUES (%s, NOW(), %s)
            ON CONFLICT (table_name)
            DO UPDATE SET load_time=NOW(), row_count=%s
        """, (table_key, row_count, row_count))

    conn.commit()


# ----------------------------
# TABLE INFERENCE
# ----------------------------
def infer_table(key):
    base = os.path.splitext(os.path.basename(key))[0].lower()
    base = re.sub(r'_[0-9]{4,14}$', '', base)
    while re.search(r'_[0-9]{4,14}$', base):
        base = re.sub(r'_[0-9]{4,14}$', '', base)

    normalized_base = re.sub(r'_(auto|consolidated|e2e_test|catalog_e2e_test|readings_e2e_test)$', '', base)

    direct_key = f"stg_{normalized_base}"
    if direct_key in TABLE_MAP:
        return direct_key

    for table_key, aliases in TABLE_ALIASES.items():
        if any(alias in normalized_base for alias in aliases):
            return table_key

    return f"stg_{normalized_base}"


# ----------------------------
# MAIN
# ----------------------------
def main():
    run_started_at = perf_counter()
    files = list_staging_files()
    run_summary = {
        'pipeline_name': 'automotive_finance_pipeline',
        'files_processed': 0,
        'rows_loaded': 0,
        'processing_time_seconds': 0.0,
        'quality_summary': {
            'files_checked': 0,
            'duplicate_records': 0,
            'total_null_values': 0,
            'schema_failures': 0,
        },
        'file_metrics': [],
        'errors': [],
    }

    if not files:
        LOGGER.info("Pipeline completion | stage=phase_4_etl | files_processed=0 | rows_loaded=0 | processing_time_seconds=0.0")
        print(f"ETL_SUMMARY::{json.dumps(run_summary)}")
        return

    LOGGER.info("Pipeline start | stage=phase_4_etl | file_count=%s", len(files))

    with psycopg2.connect(WAREHOUSE_CONN) as conn:
        with conn.cursor() as cur:
            cur.execute("SET search_path TO staging")

        for key in files:
            file_started_at = perf_counter()
            file_type = detect_file_type(key)

            try:
                table_key = infer_table(key)
                if table_key not in TABLE_MAP:
                    raise ValueError(f"No table mapping found for inferred table key {table_key}")

                LOGGER.info("File processing start | file_name=%s | file_type=%s | inferred_table=%s", key, file_type, table_key)

                raw_df = extract_file(key)
                normalized_df = normalize_column_aliases(raw_df.copy(), table_key)
                target_columns = get_table_columns(conn, TABLE_MAP[table_key])
                quality_metrics = evaluate_data_quality(normalized_df, table_key, target_columns)

                run_summary['quality_summary']['files_checked'] += 1
                run_summary['quality_summary']['duplicate_records'] += quality_metrics['duplicate_records']
                run_summary['quality_summary']['total_null_values'] += quality_metrics['total_null_values']
                if not quality_metrics['schema_validation']['is_valid']:
                    run_summary['quality_summary']['schema_failures'] += 1

                log_quality_metrics(
                    LOGGER,
                    file_name=key,
                    file_type=file_type,
                    table_name=TABLE_MAP[table_key],
                    metrics=quality_metrics,
                )

                if quality_metrics['validation_errors']:
                    raise ValueError(
                        f"Data quality validation failed for {key}: {'; '.join(quality_metrics['validation_errors'])}"
                    )

                transformed_df = transform(normalized_df, table_key)
                if transformed_df.empty:
                    raise ValueError(f"No valid rows remained after transform for {key}")

                inserted = upsert(transformed_df, table_key, conn)
                update_metadata(table_key, inserted, conn)

                file_duration = round(perf_counter() - file_started_at, 2)
                run_summary['files_processed'] += 1
                run_summary['rows_loaded'] += inserted
                run_summary['file_metrics'].append({
                    'file_name': key,
                    'file_type': file_type,
                    'table_name': TABLE_MAP[table_key],
                    'rows_processed': inserted,
                    'processing_time_seconds': file_duration,
                })

                LOGGER.info(
                    "File processing complete | file_name=%s | file_type=%s | rows_processed=%s | processing_time_seconds=%.2f",
                    key,
                    file_type,
                    inserted,
                    file_duration,
                )

            except Exception as exc:
                run_summary['errors'].append({'file_name': key, 'error': str(exc)})
                LOGGER.exception(
                    "File processing failed | file_name=%s | file_type=%s | processing_time_seconds=%.2f | error=%s",
                    key,
                    file_type,
                    perf_counter() - file_started_at,
                    exc,
                )

    run_summary['processing_time_seconds'] = round(perf_counter() - run_started_at, 2)
    LOGGER.info(
        "Pipeline completion | stage=phase_4_etl | files_processed=%s | rows_loaded=%s | processing_time_seconds=%.2f | errors=%s",
        run_summary['files_processed'],
        run_summary['rows_loaded'],
        run_summary['processing_time_seconds'],
        len(run_summary['errors']),
    )
    print(f"ETL_SUMMARY::{json.dumps(run_summary)}")

    if run_summary['errors']:
        raise RuntimeError(
            "ETL run failed due to validation or processing errors: "
            + "; ".join(f"{item['file_name']}: {item['error']}" for item in run_summary['errors'])
        )


if __name__ == "__main__":
    main()