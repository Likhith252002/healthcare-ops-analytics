# Complete Deployment Guide

End-to-end walkthrough for running the Healthcare Operations Analytics platform locally and in production.

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | `python --version` |
| PostgreSQL | 15+ | `psql --version` |
| Git | any | — |
| RAM | 4 GB+ | 8 GB recommended for Airflow |
| Disk | 10 GB+ | For DB, venv, Airflow logs |
| Docker | optional | Simplifies Prometheus/Grafana |

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone https://github.com/Likhith252002/healthcare-ops-analytics.git
cd healthcare-ops-analytics
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows
pip install --upgrade pip
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure database connection

```bash
cp .env.example .env
```

Edit `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=healthcare_ops
DB_USER=postgres
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://postgres:your_secure_password@localhost:5432/healthcare_ops
```

### 5. Create the PostgreSQL database

```bash
psql -U postgres -c "CREATE DATABASE healthcare_ops;"
```

### 6. Create schema and generate data

```bash
# Create all tables and indexes
python src/setup_database.py

# Generate 5,000 patients and 15,000+ encounters
python src/main.py
```

### 7. (Optional) Run dbt transformations

```bash
cd dbt
dbt deps
dbt run
dbt test
cd ..
```

### 8. Run data quality checks

```bash
python src/run_data_quality.py
```

All 12 checks should pass before proceeding.

### 9. Launch the Streamlit dashboard

```bash
streamlit run dashboard/app.py
```

Dashboard: **http://localhost:8501**

---

## REST API

### Start the API server

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health
- Prometheus metrics: http://localhost:8000/metrics

### Train ML models (required for prediction endpoints)

```bash
python ml/train_models.py
```

Artifacts are saved to `ml/saved_models/` and loaded automatically on API startup.

---

## Apache Airflow Orchestration

### Install and initialise

```bash
export AIRFLOW_HOME=$(pwd)/airflow
airflow db init
```

### Create admin user

```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### Configure PostgreSQL connection (Airflow UI)

1. Go to **Admin → Connections**
2. Add connection:
   - **ID:** `healthcare_ops_postgres`
   - **Type:** Postgres
   - **Host:** localhost
   - **Schema:** healthcare_ops
   - **Login:** your DB username
   - **Password:** your DB password
   - **Port:** 5432

### Start Airflow

```bash
# Terminal 1 — webserver
airflow webserver --port 8080

# Terminal 2 — scheduler
airflow scheduler
```

Airflow UI: **http://localhost:8080**

**DAGs:**
- `healthcare_etl_pipeline` — daily at 2 AM (ETL + dbt + materialized views)
- `data_quality_monitoring` — hourly (freshness + anomaly checks)

---

## Monitoring Stack

### Option A: Standalone (API-only metrics)

The API already exposes metrics at `/metrics`. Point any Prometheus instance at it:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'healthcare-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Option B: Docker (Prometheus + Grafana)

```bash
# Prometheus
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Grafana
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

In Grafana, add Prometheus as a data source (`http://host.docker.internal:9090` on Mac/Windows).

**Useful PromQL queries:**

```promql
# Request rate
rate(http_requests_total[1m])

# p95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m])

# Active patients
active_patients
```

---

## Viewing Structured Logs

All API logs are JSON on stdout:

```bash
# Pretty-print
uvicorn api.main:app 2>&1 | jq

# Filter errors
uvicorn api.main:app 2>&1 | jq 'select(.severity=="ERROR")'

# Slow requests (>200ms)
uvicorn api.main:app 2>&1 | jq 'select(.duration_seconds > 0.2)'
```

---

## Running Tests

```bash
# All tests with coverage
python -m pytest tests/ -v --cov=src --cov-report=html

# Specific suites
python -m pytest tests/test_validation.py -v
python -m pytest tests/test_retry.py -v
python -m pytest tests/test_incremental.py -v
```

**Coverage targets:** validation (11 tests), retry (8 tests), incremental (5 tests).

---

## Production Deployment

### API server with process manager

```bash
# Install supervisor (Ubuntu)
sudo apt install supervisor

# /etc/supervisor/conf.d/healthcare-api.conf
[program:healthcare-api]
command=/path/to/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 4
directory=/path/to/healthcare-ops-analytics
autostart=true
autorestart=true
stderr_logfile=/var/log/healthcare-api.err.log
stdout_logfile=/var/log/healthcare-api.out.log
```

### Nginx reverse proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass         http://127.0.0.1:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Add HTTPS with Certbot:
```bash
sudo certbot --nginx -d api.yourdomain.com
```

### Docker (single container)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
docker build -t healthcare-api .
docker run -d \
  -p 8000:8000 \
  --env-file .env \
  healthcare-api
```

### Streamlit Cloud

1. Push repository to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and connect the repo
3. Set main file: `dashboard/app.py`
4. Add secrets under **Settings → Secrets**:
   ```toml
   [database]
   host = "your-db-host"
   port = 5432
   name = "healthcare_ops"
   user = "postgres"
   password = "your-password"
   ```
5. Deploy

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_HOST` | Yes | localhost | PostgreSQL host |
| `DB_PORT` | No | 5432 | PostgreSQL port |
| `DB_NAME` | Yes | healthcare_ops | Database name |
| `DB_USER` | Yes | postgres | Database user |
| `DB_PASSWORD` | Yes | — | Database password |
| `DATABASE_URL` | No | — | Full connection string (overrides above) |

---

## Troubleshooting

| Problem | Likely cause | Fix |
|---------|-------------|-----|
| `psycopg2.OperationalError` | Wrong DB credentials | Check `.env` values |
| `ModuleNotFoundError` | venv not activated | `source venv/bin/activate` |
| Dashboard shows no data | DB not populated | Run `python src/main.py` |
| `/predict/*` returns 503 | ML models not trained | Run `python ml/train_models.py` |
| Airflow DAG not visible | DAGs folder not set | Confirm `AIRFLOW_HOME=$(pwd)/airflow` |
| `flake8` CI failures | Style issues | Run `black src/ api/ monitoring/ tests/` |

---

## Quick Reference

```bash
# Full local startup (after initial setup)
source venv/bin/activate
streamlit run dashboard/app.py &          # Dashboard → :8501
uvicorn api.main:app --reload --port 8000  # API      → :8000

# Data pipeline
python src/run_data_quality.py            # Quality checks
python src/refresh_viz_metrics.py         # Refresh views
python ml/train_models.py                 # Train ML models

# Tests
python -m pytest tests/ -v

# Airflow
export AIRFLOW_HOME=$(pwd)/airflow
airflow webserver --port 8080 &           # UI → :8080
airflow scheduler &
```
