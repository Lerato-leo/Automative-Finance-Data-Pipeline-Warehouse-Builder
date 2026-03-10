# Connection Pooling

## Goal

Phase 7 prepares the project to connect to the PostgreSQL warehouse through PgBouncer instead of opening direct database connections from every Airflow task and ETL process.

## Why PgBouncer

- limits connection spikes from Airflow scheduler, workers, and ETL runs
- reduces PostgreSQL backend connection churn
- improves stability when multiple DAG tasks or scripts connect at the same time

## Recommended Topology

```text
Airflow DAG tasks
        \
Phase 4 ETL  --->  PgBouncer  --->  PostgreSQL warehouse
        /
Ad hoc admin SQL
```

## Connection String Changes

Today the project connects directly to PostgreSQL with environment values such as:

- `DATABASE_URL_EXTERNAL`
- `DATABASE_URL_INTERNAL`
- `WAREHOUSE_CONN`

When PgBouncer is introduced, point warehouse application traffic to PgBouncer on port `6432` instead of PostgreSQL on port `5432`.

Example:

```bash
WAREHOUSE_CONN=dbname=${DB_NAME} user=${DB_USER} password=${DB_PASSWORD} host=pgbouncer port=6432
DATABASE_URL_EXTERNAL=postgresql://${DB_USER}:${DB_PASSWORD}@pgbouncer:6432/${DB_NAME}
```

## Airflow Integration

For this repo, the Airflow DAG uses `WAREHOUSE_CONN` for warehouse-facing work. Once PgBouncer is available:

1. keep Airflow metadata DB settings unchanged unless you also want to pool the metadata database
2. update only the warehouse connection variables consumed by Phase 4 and warehouse admin tasks
3. restart `airflow-scheduler`, `airflow-worker`, and `airflow-webserver`

## ETL Integration

`phase_4_python_etl/etl_main.py` uses `WAREHOUSE_CONN`. That value should be routed through PgBouncer so ETL writes no longer open direct PostgreSQL sessions.

## PgBouncer Settings To Start With

Suggested baseline:

```ini
[databases]
warehouse = host=<postgres-host> port=5432 dbname=<db-name>

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
pool_mode = transaction
default_pool_size = 20
max_client_conn = 100
ignore_startup_parameters = extra_float_digits
```

## Operational Notes

- `transaction` pooling mode is the safest default for Airflow and ETL traffic
- long-lived sessions and session-specific state should not be assumed once PgBouncer is introduced
- validate with `SHOW POOLS;` and `SHOW STATS;` in the PgBouncer admin console after rollout
