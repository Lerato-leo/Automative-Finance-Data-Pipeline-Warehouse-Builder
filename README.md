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
# Finance Data Pipeline & Warehouse

## Automotive Industry — Orion Motors (Simulated Cloud Environment)

---

## Project Overview

This project simulates a production-grade Data Engineering platform within the Finance Department of an automotive manufacturing company (Orion Motors).

The objective is to design and build an automated, cloud-native data pipeline that ingests raw financial and operational data from multiple enterprise source systems, processes it through structured ingestion and transformation layers, and loads it into a centralized Finance Data Warehouse for analytics and executive reporting.

The solution reflects modern enterprise architecture, incorporating cloud storage, ingestion automation, ELT modeling, orchestration, monitoring, and performance optimization.

---

## Project Objectives

• Design a Finance Data Warehouse using a Star Schema model
• Simulate multi-system automotive finance data sources
• Implement cloud-based raw data storage (AWS S3)
• Build ingestion pipelines using Bash & Shell scripting
• Develop Python ingestion ETL pipelines
• Implement SQL ELT transformations for warehouse modeling
• Orchestrate workflows using Apache Airflow
• Enable monitoring, logging, and alerting
• Simulate enterprise file lifecycle management

---

## Business Domain Context

**Department:** Finance
**Industry:** Automotive Manufacturing
**Company:** Orion Motors (Simulated)

### Analytical Focus Areas

• Vehicle sales revenue
• Dealer performance
• Manufacturing costs
• Operating expenses
• Customer vehicle financing
• Warranty liabilities
• Profitability analysis

---

## Executive Business Questions Answered

### Revenue Analysis

• Total revenue generated per year
• Revenue by dealer
• Revenue by vehicle model
• Monthly and yearly revenue trends

### Cost Analysis

• Cost of vehicles sold
• Dealer commission expenses
• Operating expenditure breakdown

### Profitability Analysis

• Profit per vehicle
• Profit per dealer
• Total company profit

### Financial Performance

• Best-performing dealers
• Best-selling vehicle models
• Revenue growth trends over time

---

## Source Data Systems

The warehouse integrates data from multiple simulated enterprise platforms:

| Source System    | Format       | Example Data           | Purpose              |
| ---------------- | ------------ | ---------------------- | -------------------- |
| ERP System       | CSV          | vehicle_sales.csv      | Revenue transactions |
| Manufacturing    | CSV          | vehicle_costs.csv      | Production costs     |
| Dealer Systems   | CSV / Excel  | commissions.xlsx       | Dealer payouts       |
| Accounting       | CSV          | operating_expenses.csv | OPEX tracking        |
| CRM & Financing  | JSON / Excel | customer_loans.xlsx    | Financing analytics  |
| Warranty Systems | CSV          | warranty_claims.csv    | Liability tracking   |

---

## Cloud Storage Architecture

Raw data is stored in AWS S3 buckets representing enterprise data lake storage.

Example structure:

```
s3://automotive-finance-raw-data/
	├── erp/
	├── manufacturing/
	├── dealers/
	├── accounting/
	├── financing/
	└── warranty/
```

This replaces traditional on-premise or SharePoint staging layers.

---

## Data Platform Architecture

High-level pipeline flow:

1. Source systems generate structured financial data
2. Files land in AWS S3 raw storage
3. Shell ingestion scripts monitor file arrivals
4. Python pipelines extract and clean multi-format data
5. Clean data loads into PostgreSQL staging schema
6. SQL ELT transforms staging → warehouse star schema
7. Airflow orchestrates and schedules workflows
8. Monitoring tracks pipeline health and quality

---

## Data Warehouse Modeling

The Finance Warehouse follows a Star Schema design.

### Fact Tables

• fact_vehicle_sales
• fact_operating_expenses
• fact_warranty_claims

### Dimension Tables

• dim_vehicle
• dim_dealer
• dim_customer
• dim_date

### Modeling Features

• Surrogate keys
• Slowly Changing Dimensions (SCD Type 2)
• Historical tracking
• Financial aggregations

---

## Project Phases

### Phase 1 — Data Warehouse Design

Finance domain modeling, ERDs, star schema, SCD strategy, DDL scripts.

### Phase 2 — Data Source Simulation

Faker data generation, multi-format exports, dirty data injection, source mapping.

### Phase 3 — Shell Ingestion

S3 monitoring, ingestion automation, archiving, validation, cron scheduling.

### Phase 4 — Python Ingestion ETL

Multi-format extraction, data cleaning, standardization, staging loads.

### Phase 5 — SQL ELT Modeling

Dimension builds, fact builds, surrogate key generation, business rules.

### Phase 6 — Airflow Orchestration

DAG development, sensors, operators, scheduling, retries, logging.

### Phase 7 — Streaming Pipelines

Kafka producers/consumers, real-time ingestion simulation.

### Phase 8 — Database Administration

Indexing, partitioning, backups, performance tuning.

### Phase 9 — Monitoring & Observability

Alerts, dashboards, pipeline logging, data quality tracking.

### Phase 10 — Deployment & Documentation

Dockerization, environment setup, runbooks, demos.

---

## Technology Stack

| Layer                | Technology     |
| -------------------- | -------------- |
| Cloud Storage        | AWS S3         |
| Database             | PostgreSQL     |
| ETL                  | Python         |
| ELT Modeling         | SQL            |
| Orchestration        | Apache Airflow |
| Ingestion Automation | Bash / Shell   |
| Streaming            | Apache Kafka   |
| Containerization     | Docker         |
| Version Control      | Git / GitHub   |

---

## Repository Structure (Logical)

```
phase_1_data_warehouse_design/
phase_2_data_source_setup/
phase_3_shell_ingestion/
phase_4_python_ingestion_etl/
phase_5_sql_elt_modelling/
phase_6_airflow_orchestration/
phase_7_streaming_kafka/
phase_8_database_administration/
phase_9_monitoring_logging/
phase_10_documentation_deployment/
docs/
```

Each phase represents a production data platform layer.

---

## Project Status

Active development.

Current focus:

• Warehouse schema deployment
• Staging ingestion pipelines
• S3 data lake setup
• Initial ELT transformations

Upcoming:

• Airflow orchestration
• Streaming ingestion
• Monitoring dashboards

---

## Author

**Lerato Matamela**
Associate Data Engineer — CAPACITI Programme

---

## Programme Context

Developed as part of the CAPACITI Data Engineering stream, covering:

• Linux & Shell scripting
• Data pipeline engineering
• Warehouse modeling
• Workflow orchestration
• Monitoring & observability
• Cloud data platform architecture

---

## License

This project is for educational and portfolio demonstration purposes.

See `docs/directory_explanations.md` for details on each directory.

#### Enterprise Best-Practice Justification

- **Cloud Storage First**: Raw data in S3 ensures scalability, durability, and separation from compute.
- **Layered Architecture**: Clear separation of ingestion, ETL, ELT, orchestration, monitoring, and deployment mirrors real-world enterprise platforms.
- **Documentation & Diagrams**: Centralized docs and diagrams support onboarding, maintenance, and compliance.
- **SQL ELT in Warehouse**: ELT leverages database power for transformations, supporting star schema and marts.
- **Airflow Orchestration**: Industry-standard for workflow management, retries, and scheduling.
- **Streaming Simulation**: Kafka enables real-time ingestion and event-driven architecture.
- **Monitoring & DBA**: Dedicated folders for observability and optimization ensure reliability and performance.
- **Deployment & CI/CD**: Docker and cloud configs support reproducible, scalable deployments.

### Project Status
Early development. Current focus: warehouse schema design, source data simulation, folder structure setup. Pipelines and orchestration components will be implemented in subsequent phases.

### Author
Lerato Matamela — Associate Data Engineer (CAPACITI Programme)

### Programme Context
Part of the CAPACITI Data Engineering stream, covering Linux and shell scripting, data pipeline engineering, warehouse modeling, workflow orchestration, and monitoring/deployment.
