# Monitoring & Observability

Production monitoring using Prometheus metrics and structured JSON logging.

## Metrics

### HTTP

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `http_requests_total` | Counter | method, endpoint, status | Total HTTP requests |
| `http_request_duration_seconds` | Histogram | method, endpoint | Request latency |

### Database

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `database_queries_total` | Counter | table, operation | Total DB queries |
| `database_query_duration_seconds` | Histogram | table, operation | Query duration |

### ML Models

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `ml_predictions_total` | Counter | model, status | Total predictions |
| `ml_prediction_duration_seconds` | Histogram | model | Prediction latency |

### Data Quality / ETL

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `data_quality_checks_total` | Counter | check_name, status | Quality check results |
| `etl_runs_total` | Counter | status | ETL pipeline runs |
| `etl_duration_seconds` | Histogram | — | Pipeline duration |

### Gauges (live state)

| Metric | Description |
|--------|-------------|
| `active_patients` | Current `is_current=TRUE` patient count |
| `total_encounters` | Total row count in `fact_encounters` |
| `avg_length_of_stay` | Average LOS in days (discharged encounters) |

## Accessing Metrics

```bash
# Raw Prometheus exposition format
curl http://localhost:8000/metrics

# Health check (DB + ML + system resources)
curl http://localhost:8000/health
```

### Prometheus scrape config

```yaml
scrape_configs:
  - job_name: 'healthcare-api'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

## Logging

All logs emit structured JSON to stdout.

**Example log entry:**
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "name": "root",
  "severity": "INFO",
  "message": "HTTP request",
  "method": "GET",
  "path": "/patients",
  "status_code": 200,
  "duration_seconds": 0.045
}
```

### Log levels

| Level | Use |
|-------|-----|
| DEBUG | Detailed diagnostic traces |
| INFO | Normal operational events |
| WARNING | Non-fatal issues (e.g., ML models not loaded) |
| ERROR | Failed operations |
| CRITICAL | System-threatening failures |

### Filtering logs

```bash
# All logs
uvicorn api.main:app 2>&1 | jq

# Errors only
uvicorn api.main:app 2>&1 | jq 'select(.severity=="ERROR")'

# Specific endpoint
uvicorn api.main:app 2>&1 | jq 'select(.path=="/patients")'

# Slow requests (>500ms)
uvicorn api.main:app 2>&1 | jq 'select(.duration_seconds > 0.5)'
```

## Production Setup

### 1. Deploy Prometheus

```bash
docker run -d \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus
```

### 2. Deploy Grafana

```bash
docker run -d \
  -p 3000:3000 \
  grafana/grafana
```

Connect Prometheus as a data source at `http://localhost:9090`.

**Dashboard panels to create:**
- Request rate (requests/sec) — `rate(http_requests_total[1m])`
- p95 latency — `histogram_quantile(0.95, http_request_duration_seconds_bucket)`
- Error rate — `rate(http_requests_total{status=~"5.."}[5m])`
- Active patients — `active_patients`
- ML prediction latency — `histogram_quantile(0.95, ml_prediction_duration_seconds_bucket)`

### 3. Alert rules

```yaml
groups:
  - name: healthcare_api
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate: >5% of requests returning 5xx"

      - alert: SlowAPIResponse
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1.0
        for: 5m
        annotations:
          summary: "API p95 latency > 1s"

      - alert: MLPredictionErrors
        expr: rate(ml_predictions_total{status="error"}[5m]) > 0
        for: 2m
        annotations:
          summary: "ML prediction errors detected"

      - alert: DataStale
        expr: (time() - avg_length_of_stay) > 86400
        annotations:
          summary: "Gauge metrics not refreshed in >24 hours — ETL may be stuck"
```

### 4. Log aggregation

**Loki (lightweight, Grafana-native):**
```bash
docker run -d -p 3100:3100 grafana/loki
```
Then add Loki as a data source in Grafana and query with LogQL:
```logql
{job="healthcare-api"} | json | severity = "ERROR"
```

**ELK Stack:** Ship stdout JSON to Logstash → Elasticsearch → Kibana.

## Health Check Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:45.123456",
  "uptime_seconds": 3600.0,
  "checks": {
    "database": "ok",
    "ml_models": "ok"
  },
  "system": {
    "cpu_percent": 12.5,
    "memory_percent": 48.2,
    "memory_available_gb": 6.14
  }
}
```

`status` is `"healthy"` when the database check passes, `"degraded"` otherwise.
