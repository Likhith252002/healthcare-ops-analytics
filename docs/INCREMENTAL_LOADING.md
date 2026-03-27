# Incremental Data Loading Guide

## Overview

Incremental loading processes only new or changed data instead of reloading entire datasets. This dramatically improves performance and reduces resource usage.

## Why Incremental Loading?

**Full Load (every time):**
- ❌ Processes all 1M records every hour
- ❌ Takes 30 minutes to complete
- ❌ High database load
- ❌ Slow for end users

**Incremental Load:**
- ✅ Processes only 1,000 new records per hour
- ✅ Takes 30 seconds to complete
- ✅ Low database impact
- ✅ Near real-time data freshness

## Core Patterns

### Pattern 1: Timestamp-Based Loading

Load records created/updated since last run.

**Requirements:**
- Source table has `created_at` or `updated_at` timestamp
- Timestamps are reliable and monotonically increasing

**Implementation:**
```python
from utils.incremental import get_last_load_timestamp, record_load_metadata
from datetime import datetime

# Get watermark (last loaded timestamp)
last_load = get_last_load_timestamp('fact_encounters', 'created_at')

# Query source for new records
new_records = query_source(
    "SELECT * FROM source_encounters WHERE created_at > %s",
    last_load or datetime(1900, 1, 1)  # Full load if None
)

# Load new records
start_time = datetime.now()
load_records(new_records)
end_time = datetime.now()

# Record load metadata
record_load_metadata('fact_encounters', len(new_records), start_time, end_time)
```

### Pattern 2: Change Data Capture (CDC)

Compare source and target to detect changes.

**Requirements:**
- Source and target have matching business keys
- Ability to compare field values

**Implementation:**
```python
from utils.incremental import detect_changes

# Fetch current data from source
source_data = fetch_from_source()

# Detect what changed
changes = detect_changes(
    table_name='dim_patients',
    source_data=source_data,
    key_column='patient_id',
    compare_columns=['address', 'city', 'phone_number']
)

# Process each category
insert_records(changes['new'])
update_records(changes['updated'])
# Skip changes['unchanged'] - no action needed
```

### Pattern 3: Incremental + SCD2

Combine incremental loading with Type 2 SCD for history tracking.

**Implementation:**
```python
from utils.incremental import detect_changes
from utils.scd2_handler import update_patient_scd2

# Detect changes
changes = detect_changes(
    'dim_patients',
    source_data,
    key_column='patient_id',
    compare_columns=['address', 'city', 'insurance_type']
)

# Insert new patients
for patient in changes['new']:
    insert_patient(patient)

# Update changed patients using SCD2
for patient in changes['updated']:
    update_patient_scd2(
        patient_id=patient['patient_id'],
        changes={col: patient[col] for col in compare_columns},
        effective_date=datetime.now()
    )

# Unchanged patients - no action
```

## Load Metadata Tracking

Track load history for monitoring and troubleshooting.

### Load History Table
```sql
CREATE TABLE load_history (
    load_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    records_loaded INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    duration_seconds NUMERIC(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Monitoring Queries
```sql
-- Recent loads
SELECT * FROM load_history
ORDER BY created_at DESC
LIMIT 10;

-- Load performance trend
SELECT
    table_name,
    DATE(start_time) AS load_date,
    SUM(records_loaded) AS total_records,
    AVG(duration_seconds) AS avg_duration,
    COUNT(*) AS load_count
FROM load_history
GROUP BY table_name, DATE(start_time)
ORDER BY load_date DESC;

-- Failed loads (no records despite source having data)
SELECT * FROM load_history
WHERE records_loaded = 0
  AND created_at > CURRENT_DATE - INTERVAL '7 days';
```

## Best Practices

### 1. Idempotency

Ensure loads can be re-run without duplicating data.
```python
# Use UPSERT (INSERT ... ON CONFLICT UPDATE)
INSERT INTO dim_patients (patient_id, first_name, last_name, ...)
VALUES (%s, %s, %s, ...)
ON CONFLICT (patient_id)
DO UPDATE SET
    first_name = EXCLUDED.first_name,
    last_name = EXCLUDED.last_name,
    updated_at = CURRENT_TIMESTAMP;
```

### 2. Backfill Strategy

Handle late-arriving data.
```python
# Include lookback window
lookback_hours = 24
last_load = get_last_load_timestamp('fact_encounters')
load_from = last_load - timedelta(hours=lookback_hours)

# This catches records that were created after last load
# but had timestamps in the past
```

### 3. Validate Watermarks

Ensure timestamps don't go backward.
```python
last_load = get_last_load_timestamp('fact_encounters')
current_max = get_current_max_timestamp_from_source()

if current_max < last_load:
    logger.warning(
        f"Source max timestamp ({current_max}) is less than "
        f"last load timestamp ({last_load}). Possible data issue!"
    )
```

### 4. Batch Incremental Loads

Even incremental loads should batch commits.
```python
batch_size = 1000
for i in range(0, len(new_records), batch_size):
    batch = new_records[i:i+batch_size]
    insert_batch(batch)
    conn.commit()
```

## Performance Comparison

**Example: 1M patient records, 1K new per day**

| Strategy | Records Processed | Time | Frequency |
|----------|------------------|------|-----------|
| Full reload | 1,000,000 | 30 min | Daily |
| Incremental | 1,000 | 30 sec | Hourly |

**Improvement:** 60x faster, 24x more frequent updates

## Scheduling Incremental Loads

### Cron (Hourly)
```bash
0 * * * * cd /path/to/project && python src/incremental_load.py
```

### Airflow DAG
```python
from airflow import DAG
from airflow.operators.python import PythonOperator

dag = DAG('incremental_load', schedule_interval='@hourly')

load_task = PythonOperator(
    task_id='load_encounters',
    python_callable=incremental_load_encounters,
    dag=dag
)
```

## Troubleshooting

### No records loaded despite source having data

**Causes:**
- Watermark timestamp ahead of source data
- Time zone mismatch
- Clock drift between systems

**Solution:**
```python
# Reset watermark manually
DELETE FROM load_history WHERE table_name = 'fact_encounters';
```

### Duplicate records

**Causes:**
- No unique key constraint
- Concurrent loads
- Failed transaction rollback

**Solution:**
- Add unique constraints
- Use advisory locks for concurrency
- Implement UPSERT logic
