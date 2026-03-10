# Restore Procedure

## Backup Format

The warehouse backup script creates gzip-compressed logical SQL backups using `pg_dump` in plain-text format:

```bash
phase_7_database_administration/backups/warehouse_backup_YYYYMMDD_HHMMSS.sql.gz
```

This format is intentional so restore operations can be executed with `psql`.

## Restore Prerequisites

- PostgreSQL client tools installed locally
- network access to the warehouse database
- valid `DB_HOST` or `DB_HOST_EXTERNAL`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
- the target database already created if restoring to a new environment

## Restore Into The Existing Warehouse

```bash
gunzip -c phase_7_database_administration/backups/warehouse_backup_YYYYMMDD_HHMMSS.sql.gz \
  | PGPASSWORD="$DB_PASSWORD" psql \
      -h "$DB_HOST_EXTERNAL" \
      -p "$DB_PORT" \
      -U "$DB_USER" \
      -d "$DB_NAME"
```

## Restore Into A Fresh Database

```bash
createdb -h "$DB_HOST_EXTERNAL" -p "$DB_PORT" -U "$DB_USER" automotive_warehouse_restore_test

gunzip -c phase_7_database_administration/backups/warehouse_backup_YYYYMMDD_HHMMSS.sql.gz \
  | PGPASSWORD="$DB_PASSWORD" psql \
      -h "$DB_HOST_EXTERNAL" \
      -p "$DB_PORT" \
      -U "$DB_USER" \
      -d automotive_warehouse_restore_test
```

## Post-Restore Validation

Run these checks after the restore:

```sql
SELECT current_database();
SELECT COUNT(*) FROM staging.staging_payments;
SELECT COUNT(*) FROM staging.staging_interactions;
SELECT COUNT(*) FROM warehouse.fact_payments;
SELECT COUNT(*) FROM warehouse.fact_telemetry;
```

Also verify that expected schemas exist:

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('staging', 'warehouse');
```

## Restore Test Recommendation

- schedule the backup script daily
- perform a restore test at least monthly
- keep the most recent successful restore-test timestamp with operations notes outside the repo
