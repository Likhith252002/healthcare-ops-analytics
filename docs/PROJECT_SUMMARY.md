# Healthcare Operations Analytics - Project Summary

## Project Overview

End-to-end healthcare analytics platform demonstrating:
- Data engineering (ETL pipeline)
- Data warehousing (dimensional modeling)
- Analytics engineering (dbt transformations)
- Business intelligence (Streamlit dashboard)
- Predictive analytics (ML-ready features)

**Built for:** Data analyst/engineer portfolio and job applications

---

## Architecture

```
Raw Data Generation
        ↓
  PostgreSQL (Star Schema)
  ├── dim_patients   (SCD Type 2)
  ├── dim_departments
  ├── dim_physicians
  ├── fact_encounters
  └── fact_bed_events
        ↓
  dbt Transformation Layer
  ├── staging/       (clean + standardize)
  ├── intermediate/  (join + enrich)
  └── marts/         (aggregate for reporting)
        ↓
  Materialized Views (pre-aggregated metrics)
        ↓
  Streamlit Dashboard (6 pages)
```

---

## Components Built

### 1. Data Generation Pipeline
- **1,000 synthetic patients** with realistic demographics (Faker)
- **6 hospital departments** with bed capacities
- **50 physicians** distributed by specialty
- **5,000 encounters** over 90 days with realistic admission patterns
- **10,000 bed events** (assigned/discharged per encounter)
- Total: ~16,000 records

### 2. Database Schema (Star Schema)
- Kimball dimensional modeling methodology
- SCD Type 2 on `dim_patients` (tracks demographic history)
- Foreign key relationships with referential integrity
- Strategic indexes on filter and join columns

### 3. Data Quality Framework
- 12 automated tests: NULL checks, referential integrity, business rules, SCD2 consistency
- Severity levels (error vs warning)
- Runs as part of main pipeline via `python src/run_data_quality.py`

### 4. Analytics SQL Library
- ER wait time analysis with percentiles
- Bed utilization with hourly occupancy
- Length of stay by department and admission type
- Advanced window functions: LEAD/LAG, RANK, NTILE, running totals
- 30-day readmission cohort analysis
- Recursive CTE bed timeline

### 5. dbt Transformation Layer
- Staging models: clean + standardize raw tables
- Intermediate models: join and enrich
- Mart models: aggregate for reporting
- Column-level tests in schema.yml

### 6. Materialized Views (BI Layer)
- `mv_daily_hospital_snapshot` — daily KPIs
- `mv_department_performance` — department metrics
- `mv_patient_demographics` — population breakdown
- `mv_weekly_trends` — week-over-week changes
- `mv_top_complaints` — chief complaint rankings
- Refresh script: `python src/refresh_viz_metrics.py`

### 7. Production Utilities
- **Retry with exponential backoff** (`src/utils/retry.py`)
- **Circuit breaker pattern** (`src/utils/circuit_breaker.py`)
- **Input validation** (`src/utils/validation.py`)
- **Incremental loading** (`src/utils/incremental.py`)
- **Load history tracking** (`load_history` table)
- **SCD2 handler** (`src/utils/scd2_handler.py`)
- **Performance benchmarking** (`src/benchmark_queries.py`)

### 8. Testing & CI/CD
- 24 unit tests across 3 test files
- Mocked database connections (no external deps in unit tests)
- GitHub Actions CI pipeline (ubuntu + postgres:15 service)
- Runs on every push to main and all pull requests

### 9. Streamlit Dashboard (6 Pages)
- **Home:** KPI overview, 30-day trend, admission type distribution
- **Operations:** KPIs, daily trends, department volume, LOS distribution, hourly patterns
- **Patients:** Demographics (4 charts), patient search, visit patterns, readmission tracking
- **Departments:** Comparison view + individual drill-down, 8-column metrics table
- **Analytics:** Statistical summary (8 metrics), weekly/daily/hourly trends, cohort retention
- **Predictions:** Readmission risk calculator (0-100), LOS forecaster with confidence intervals

---

## Key Technical Decisions

| Decision | Choice | Reason |
|---|---|---|
| Database | PostgreSQL 15 | Industry standard, advanced SQL features |
| ORM/Driver | psycopg2 | Direct control, no ORM overhead |
| Data Generation | Faker + random.choices | Realistic distributions without real PHI |
| Dashboard | Streamlit | Rapid development, Python-native |
| Charts | Plotly | Interactive, professional appearance |
| CI/CD | GitHub Actions | Free, integrates with repo |
| Deployment | Docker + Streamlit Cloud | Flexible, demo-friendly |

---

## Skills Demonstrated

### Data Engineering
- ETL pipeline design and implementation
- Batch processing with configurable sizes
- Incremental loading patterns
- Data quality testing

### SQL & Databases
- Star schema / dimensional modeling (Kimball)
- SCD Type 2 implementation
- Window functions (LEAD, LAG, RANK, NTILE, PERCENT_RANK)
- CTEs and recursive CTEs
- Materialized views with indexes
- PERCENTILE_CONT, generate_series

### Python
- OOP design patterns
- Decorator pattern (retry, backoff)
- Context managers (performance timing)
- Mocking in unit tests
- Streamlit app development

### Analytics
- Cohort analysis
- Readmission rate calculation
- Statistical summaries (mean, median, IQR, stddev)
- Trend analysis and forecasting
- Risk scoring models

### Software Engineering
- Modular code structure
- Error handling and resilience
- Automated testing (24 unit tests)
- CI/CD pipeline
- Documentation (README, guides, API docs)
- Git workflow with meaningful commits

---

## Project Statistics

| Metric | Value |
|---|---|
| Python files | 25+ |
| SQL files | 15+ |
| Lines of code | ~5,000+ |
| Database tables | 5 core + materialized views |
| Dashboard pages | 6 |
| Interactive charts | 20+ |
| Unit tests | 24 |
| Documentation files | 12+ |
| Git commits | 15+ |

---

## How to Run

```bash
# 1. Clone and setup
git clone https://github.com/Likhith252002/healthcare-ops-analytics
cd healthcare-ops-analytics
pip install -r requirements.txt
cp .env.example .env  # add DB credentials

# 2. Generate data
python src/main.py

# 3. Create materialized views
psql -d healthcare_ops -f sql/viz/dashboard_metrics.sql

# 4. Launch dashboard
streamlit run dashboard/app.py
```
