# Data Visualization Layer

Pre-aggregated metrics optimized for dashboards and BI tools.

## Materialized Views

Materialized views store query results physically, enabling fast dashboard loading without recalculating aggregations on every request.

### Available Metrics

#### 1. **mv_daily_hospital_snapshot**
Daily hospital-wide KPIs for trend analysis.

**Columns:**
- `metric_date` - Date of metrics
- `total_admissions` - Daily admission count
- `unique_patients` - Distinct patients admitted
- `avg_length_of_stay` - Average LOS in days
- `emergency_admissions`, `scheduled_admissions` - By admission type
- `beds_assigned`, `beds_released` - Bed activity
- `emergency_pct` - Percentage of admissions that are emergency
- `weekday_flag` - Weekend vs Weekday

**Use cases:**
- Daily volume charts
- Emergency vs scheduled trends
- Weekday/weekend patterns
- Rolling averages

**Example query:**
```sql
-- Last 30 days trend
SELECT * FROM mv_daily_hospital_snapshot
WHERE metric_date > CURRENT_DATE - 30
ORDER BY metric_date;
```

#### 2. **mv_department_performance**
Current performance metrics by department.

**Columns:**
- Department identifiers and metadata
- `total_encounters`, `unique_patients` - Volume metrics
- `avg_length_of_stay`, `median_length_of_stay` - LOS metrics
- `bed_utilization_pct` - Capacity utilization
- `encounters_per_physician` - Workload distribution
- `emergency_pct`, `discharge_pct` - Outcome percentages

**Use cases:**
- Department comparison dashboards
- Capacity planning
- Resource allocation
- Performance scorecards

**Example query:**
```sql
-- Departments sorted by utilization
SELECT department_name, bed_utilization_pct, total_encounters
FROM mv_department_performance
ORDER BY bed_utilization_pct DESC;
```

#### 3. **mv_patient_demographics**
Patient population distribution metrics.

**Columns:**
- `age_group` - Categorized age ranges
- `gender`, `insurance_type`, `state` - Demographics
- `patient_count` - Count in each segment
- `pct_of_total_patients` - Overall percentage
- `pct_within_age_group` - Percentage within age cohort

**Use cases:**
- Population health dashboards
- Insurance mix analysis
- Geographic distribution maps
- Age/gender pyramids

**Example query:**
```sql
-- Top insurance types by age group
SELECT age_group, insurance_type, patient_count
FROM mv_patient_demographics
ORDER BY age_group, patient_count DESC;
```

#### 4. **mv_weekly_trends**
Weekly aggregations for time-series analysis.

**Columns:**
- `week_start`, `week_end` - Week boundaries
- `weekly_admissions`, `unique_patients` - Volume
- `avg_length_of_stay` - LOS
- `emergency_admissions`, `scheduled_admissions` - By type
- `wow_admissions_change`, `wow_admissions_pct_change` - Week-over-week

**Use cases:**
- Trend charts
- Seasonality analysis
- Growth tracking
- Forecasting inputs

**Example query:**
```sql
-- Last 12 weeks with WoW change
SELECT week_start, weekly_admissions, wow_admissions_pct_change
FROM mv_weekly_trends
ORDER BY week_start DESC
LIMIT 12;
```

#### 5. **mv_top_complaints**
Most common chief complaints.

**Columns:**
- `chief_complaint` - Admission reason
- `encounter_count`, `unique_patients` - Volume
- `avg_los_days` - LOS for this complaint
- `emergency_count` - How many were emergencies
- `pct_of_total_encounters` - Percentage of all encounters
- `complaint_rank` - Rank by frequency

**Use cases:**
- Top diagnoses charts
- Clinical focus areas
- Resource planning by complaint
- Triage optimization

**Example query:**
```sql
-- Top 10 complaints
SELECT complaint_rank, chief_complaint, encounter_count, emergency_count
FROM mv_top_complaints
ORDER BY complaint_rank
LIMIT 10;
```

## Refresh Strategy

### Manual Refresh

Refresh all views:
```bash
python src/refresh_viz_metrics.py
```

Or refresh individual views in SQL:
```sql
REFRESH MATERIALIZED VIEW mv_daily_hospital_snapshot;
```

### When to Refresh

- After bulk data loads (e.g., daily ETL)
- Before dashboard deployment
- When data quality issues are fixed
- On-demand when users request latest data

### Refresh Performance

Current refresh times (16K records):
- `mv_daily_hospital_snapshot`: <1 second
- `mv_department_performance`: <1 second
- `mv_patient_demographics`: <1 second
- `mv_weekly_trends`: <1 second
- `mv_top_complaints`: <1 second

**Total refresh time:** ~3-5 seconds for all views

### Automated Refresh (Production)

**Option 1: Cron job**
```bash
# Refresh every night at 2 AM
0 2 * * * cd /path/to/project && python src/refresh_viz_metrics.py
```

**Option 2: Airflow DAG**
```python
refresh_metrics = PythonOperator(
    task_id='refresh_viz_metrics',
    python_callable=refresh_all_metrics,
    dag=dag
)
```

## BI Tool Integration

### Streamlit
```python
import streamlit as st
import psycopg2
import pandas as pd

@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_daily_snapshot():
    conn = psycopg2.connect(...)
    df = pd.read_sql("SELECT * FROM mv_daily_hospital_snapshot", conn)
    conn.close()
    return df
```

### Tableau / PowerBI
Connect to PostgreSQL and query materialized views directly — they appear as regular tables. Schedule dataset refresh after running `refresh_viz_metrics.py`.

### Performance Benefits

| Approach | Query Time | DB CPU |
|---|---|---|
| Without materialized views | ~500ms | High |
| With materialized views | ~5ms | Minimal |

**~100x faster dashboard loading.**

## Best Practices

1. **Refresh regularly:** Keep metrics current after each data load
2. **Monitor size:** Use `pg_size_pretty(pg_total_relation_size(...))` to track growth
3. **Index on filter columns:** Date indexes already added for time-range queries
4. **Document data freshness:** Users should know when views were last refreshed
5. **Large datasets:** Use `REFRESH MATERIALIZED VIEW CONCURRENTLY` to avoid locking
