# Airflow Orchestration

## Overview

Apache Airflow manages automated ETL pipelines and monitoring.

**DAGs:**
- `healthcare_etl_pipeline` - Daily ETL (runs 2 AM)
- `data_quality_monitoring` - Hourly monitoring

## Setup

### 1. Install Airflow
```bash
pip install apache-airflow apache-airflow-providers-postgres
```

### 2. Initialize Airflow Database
```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
```

### 3. Create Admin User
```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### 4. Configure Connection
```bash
# Add PostgreSQL connection in Airflow UI
# Connection ID: healthcare_ops_postgres
# Connection Type: Postgres
# Host: localhost
# Schema: healthcare_ops
# Login: your_username
# Password: your_password
# Port: 5432
```

### 5. Start Airflow
```bash
# Start webserver (terminal 1)
airflow webserver --port 8080

# Start scheduler (terminal 2)
airflow scheduler
```

**Access UI:** http://localhost:8080

## DAG Details

### healthcare_etl_pipeline

**Schedule:** Daily at 2 AM
**Tasks:**
1. Data quality checks
2. Generate incremental data
3. Run dbt models
4. Run dbt tests
5. Refresh materialized views
6. Update table statistics
7. Validate results

**Runtime:** ~10-15 minutes

### data_quality_monitoring

**Schedule:** Hourly
**Tasks:**
1. Check data freshness (alert if >48 hours)
2. Check for anomalies (unusual patterns)

**Runtime:** ~2 minutes

## Manual Trigger
```bash
# Trigger ETL pipeline
airflow dags trigger healthcare_etl_pipeline

# Test specific task
airflow tasks test healthcare_etl_pipeline data_quality_checks 2024-01-01
```

## Monitoring

**Airflow UI Sections:**
- DAGs: View all workflows
- Grid: Execution history
- Graph: Task dependencies
- Logs: Task output

**Key Metrics:**
- Success rate
- Task duration
- Retry frequency

## Production Deployment

### Docker Compose
See official Airflow documentation for docker-compose setup.

### Cloud Options
- AWS MWAA (Managed Workflows for Apache Airflow)
- Google Cloud Composer
- Astronomer
