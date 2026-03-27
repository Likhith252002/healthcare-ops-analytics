# Dashboard Deployment Guide

## Local Development

### Prerequisites
- Python 3.11+
- PostgreSQL database running
- Data populated (run `python src/main.py`)

### Setup

1. **Install dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure database connection**
```bash
# Option 1: Use .env file (recommended for local)
cp .env.example .env
# Edit .env with your database credentials

# Option 2: Use Streamlit secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets.toml with your database credentials
```

3. **Run dashboard**
```bash
streamlit run dashboard/app.py
```

Dashboard opens at: http://localhost:8501

## Streamlit Cloud Deployment

### Step 1: Push to GitHub
```bash
git push origin main
```

### Step 2: Deploy on Streamlit Cloud

1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `your-username/healthcare-ops-analytics`
5. Main file path: `dashboard/app.py`
6. Click "Deploy"

### Step 3: Configure Secrets

In Streamlit Cloud dashboard:
1. Go to app settings → Secrets
2. Add database credentials:
```toml
[postgres]
host = "your-db-host.com"
port = "5432"
database = "healthcare_ops"
user = "your_username"
password = "your_password"
```

3. Save and redeploy

## Docker Deployment

### Build Image
```bash
docker build -t healthcare-dashboard .
```

### Run Container
```bash
docker run -p 8501:8501 \
  -e DB_HOST=your-db-host \
  -e DB_PORT=5432 \
  -e DB_NAME=healthcare_ops \
  -e DB_USER=your_username \
  -e DB_PASSWORD=your_password \
  healthcare-dashboard
```

### Docker Compose
```yaml
version: '3.8'
services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=healthcare_ops
      - DB_USER=postgres
      - DB_PASSWORD=postgres
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=healthcare_ops
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Run with: `docker-compose up`

## Performance Optimization

### Caching
Dashboard uses `@st.cache_data` for expensive queries. Cache TTL: 1 hour.

To clear cache: Settings → Clear cache in dashboard

### Database Connection Pooling
For production, use connection pooling:
```python
# utils/db_connection.py
from psycopg2 import pool

connection_pool = pool.SimpleConnectionPool(1, 20, **db_params)
```

### Resource Limits
Streamlit Cloud free tier:
- 1 GB RAM
- 1 CPU core
- Limited to 3 apps

For production: Upgrade to Streamlit Cloud Pro or self-host.

## Troubleshooting

### "Connection refused"
- Check database is running
- Verify firewall allows connections on port 5432
- Check .env or secrets.toml has correct credentials

### "Module not found"
```bash
pip install -r requirements.txt
```

### Slow loading
- Check database query performance
- Use materialized views: `python src/refresh_viz_metrics.py`
- Reduce time period in dashboard selectors

### Dashboard won't start
Check logs:
```bash
streamlit run dashboard/app.py --logger.level=debug
```
