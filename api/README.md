# Healthcare Operations API

RESTful API built with FastAPI for programmatic access to healthcare data and ML predictions.

**Base URL:** http://localhost:8000
**Interactive Docs:** http://localhost:8000/docs
**ReDoc:** http://localhost:8000/redoc

## Running the API

```bash
# Development (auto-reload)
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Endpoints

### Health Check

**GET /**
```bash
curl http://localhost:8000/
```
```json
{
  "status": "healthy",
  "api": "Healthcare Operations API",
  "version": "1.0.0",
  "ml_models_available": true
}
```

### Patients

**GET /patients** — List patients (paginated)

| Param | Type | Default | Range |
|-------|------|---------|-------|
| `limit` | int | 100 | 1–1000 |
| `offset` | int | 0 | ≥0 |

```bash
curl "http://localhost:8000/patients?limit=10&offset=0"
```

**GET /patients/{patient_id}** — Get a specific patient
```bash
curl http://localhost:8000/patients/P-0001
```
Returns 404 if not found.

### Encounters

**GET /encounters** — List encounters

| Param | Type | Default |
|-------|------|---------|
| `patient_id` | str (optional) | — |
| `limit` | int | 100 |

```bash
# All encounters
curl "http://localhost:8000/encounters?limit=50"

# Patient-specific
curl "http://localhost:8000/encounters?patient_id=P-0001"
```

### Departments

**GET /departments** — List all departments
```bash
curl http://localhost:8000/departments
```

### Statistics

**GET /stats/summary** — Summary statistics
```bash
curl http://localhost:8000/stats/summary
```
```json
{
  "total_patients": 5000,
  "total_encounters": 15234,
  "total_departments": 10,
  "total_physicians": 30,
  "avg_los_days": 3.42
}
```

### ML Predictions

> Requires trained models. Run `python ml/train_models.py` first.

**POST /predict/readmission** — 30-day readmission risk

```bash
curl -X POST http://localhost:8000/predict/readmission \
  -H "Content-Type: application/json" \
  -d '{
    "age": 65,
    "is_male": 1,
    "is_emergency": 1,
    "is_uninsured": 0,
    "los_days": 4.5,
    "prior_visits": 2
  }'
```
```json
{
  "risk_score": 73.2,
  "prediction": "High Risk",
  "probability": 0.732
}
```

Risk levels: **High Risk** (≥70%), **Medium Risk** (40–70%), **Low Risk** (<40%)

**POST /predict/los** — Length of stay prediction

```bash
curl -X POST http://localhost:8000/predict/los \
  -H "Content-Type: application/json" \
  -d '{
    "age": 45,
    "is_male": 0,
    "is_emergency": 0,
    "bed_capacity": 50,
    "day_of_week": 2,
    "hour_of_day": 14
  }'
```
```json
{
  "predicted_los": 3.2,
  "confidence_interval": [2.6, 3.8]
}
```

The confidence interval is a 95% CI derived from the variance across Random Forest tree predictions.

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# List patients
patients = requests.get(f"{BASE_URL}/patients?limit=5").json()

# Predict readmission risk
payload = {
    "age": 70,
    "is_male": 1,
    "is_emergency": 1,
    "is_uninsured": 0,
    "los_days": 5.0,
    "prior_visits": 3,
}
result = requests.post(f"{BASE_URL}/predict/readmission", json=payload).json()
print(f"Risk Score: {result['risk_score']}%  ({result['prediction']})")
```

## Production Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Authentication

Currently open. For production, add:
- API key header (`X-API-Key`) via FastAPI `Security` dependency
- Rate limiting with `slowapi`
- HTTPS via Nginx/Certbot
