# Finance Data Pipeline & Warehouse

## Automotive Industry — Orion Motors (Simulated Environment)

### Project Overview
This project simulates a real-world Data Engineering environment within the Finance Department of an automotive company (Orion Motors). The objective is to design and build an automated data pipeline that ingests raw financial data from multiple upstream systems, transforms it, and loads it into a centralized finance data warehouse for reporting and analytics. The solution follows enterprise data engineering practices, including structured ingestion, orchestration, monitoring, and warehouse modeling.

### Project Objectives
- Design a Finance Data Warehouse using a Star Schema model
- Simulate multi-system financial data sources
- Build automated ingestion pipelines using Bash & Shell scripting
- Develop ETL processes for data transformation and loading
- Orchestrate workflows using Apache Airflow
- Implement monitoring, logging, and scheduling
- Simulate real-world file lifecycle management

### Business Domain
- Department: Finance
- Industry: Automotive Manufacturing
- Company: Orion Motors (Simulated)
- Analysis focus: revenue and invoices, operational expenses, budget vs actuals, supplier procurement costs, customer vehicle financing, warranty and service liabilities

### Data Source Systems
Data is sourced from multiple simulated enterprise systems:

| Source System | Format | Example Files | Warehouse Usage |
| --- | --- | --- | --- |
| ERP System | CSV | invoices.csv, payments.csv | Financial transactions |
| Supplier Management | JSON | supplier_contracts.json | Supplier costs and performance |
| Sales Financing | Excel | customer_loans.xlsx | Customer finance analytics |
| Warranty Systems | CSV / Excel | warranty_claims.csv | Service liabilities |

### SharePoint Staging Layer
- Source exports land in company SharePoint folders before ingestion.
- Represents enterprise document management and controlled intake.
- SharePoint serves as the intake layer before automated processing begins.

### Ingestion Architecture (High Level)
1) Source systems generate structured financial data.
2) Normalized exports are stored in SharePoint.
3) Files synchronize to local ingestion folders.
4) Bash scripts monitor and manage file lifecycle.
5) ETL pipelines process and transform data.
6) Cleaned data loads into PostgreSQL warehouse.
7) Airflow orchestrates and schedules workflows.

### Project Phases
- Phase 1 — Data Warehouse Design: finance domain modeling, star schema design, fact/dimension tables, SCD Type 2, SQL schema creation.
- Phase 2 — Data Source Simulation: generate CSV/JSON/Excel, simulate daily drops, inject dirty data, map sources to warehouse tables.
- Phase 3 — Shell Scripting Ingestion: folder monitoring, validation, staging, archiving, logging/notifications, cron scheduling.
- Phase 4 — Python ETL Development: extract multi-format data, transform/clean, apply business logic, load warehouse.
- Phase 5 — Airflow Orchestration: DAG design, task dependencies, sensors/operators, monitoring, retries.
- Phases 6+: streaming, DBA optimization, monitoring, deployment.

### Tools & Technologies
- Database: PostgreSQL
- Orchestration: Apache Airflow
- Scripting: Bash / Shell
- ETL Development: Python
- Data Generation: Faker
- Containerization: Docker
- Version Control: Git and GitHub

### Repository Structure
- phase_1/: warehouse design and schema
- phase_2/: source data simulation
- phase_3/: Bash ingestion scripts
- phase_4/: Python ETL pipelines
- phase_5/: Airflow DAG orchestration
- phase_6+/: streaming, monitoring, deployment

### Project Status
Early development. Current focus: warehouse schema design, source data simulation, folder structure setup. Pipelines and orchestration components will be implemented in subsequent phases.

### Author
Lerato Matamela — Associate Data Engineer (CAPACITI Programme)

### Programme Context
Part of the CAPACITI Data Engineering stream, covering Linux and shell scripting, data pipeline engineering, warehouse modeling, workflow orchestration, and monitoring/deployment.
