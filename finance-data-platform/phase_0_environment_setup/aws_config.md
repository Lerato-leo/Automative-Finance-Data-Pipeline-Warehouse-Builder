# AWS S3 Bucket Configuration

## Buckets
- automotive-raw-data-lerato-2026
- automotive-staging-data-lerato-2026
- automotive-archive-data-lerato-2026

## Folder Structure Example

```
automotive-raw-data-lerato-2026/
  ├── erp/
  ├── crm/
  ├── finance/
  ├── suppliers/
  ├── iot/

automotive-staging-data-lerato-2026/
  ├── cleaned/
  ├── normalized/

automotive-archive-data-lerato-2026/
  ├── historical/
```

- **Bronze:** Raw, messy files (CSV, JSON, Excel)
- **Silver:** Cleaned, normalized parquet/tables
- **Archive:** Historical backups
