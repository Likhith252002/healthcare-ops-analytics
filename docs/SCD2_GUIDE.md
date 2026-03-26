# Type 2 Slowly Changing Dimensions - Implementation Guide

## What is SCD Type 2?

Type 2 Slowly Changing Dimensions preserve the complete history of changes to dimensional data. Instead of updating records in place (which loses history), SCD2:

1. **Expires** the old record (sets `valid_to` date, `is_current = FALSE`)
2. **Inserts** a new record with updated values (new `valid_from` date, `is_current = TRUE`)

This enables:
- ✓ Historical reporting ("what was the patient's address in December 2025?")
- ✓ Complete audit trails
- ✓ Point-in-time analysis
- ✓ Trend analysis over time

## Schema Design

### Key Columns

| Column | Type | Purpose |
|--------|------|---------|
| `patient_key` | SERIAL | Surrogate key (increments with each version) |
| `patient_id` | VARCHAR | Business key (same across all versions) |
| `valid_from` | TIMESTAMP | When this version became active |
| `valid_to` | TIMESTAMP | When this version expired (9999-12-31 if current) |
| `is_current` | BOOLEAN | TRUE for active record, FALSE for historical |
| `record_version` | INTEGER | Version number (1, 2, 3, ...) |

### Important Indexes
```sql
-- Fast lookup of current records
CREATE INDEX idx_patients_business_key_current
ON dim_patients(patient_id, is_current);

-- Fast point-in-time queries
CREATE INDEX idx_patients_valid_dates
ON dim_patients(valid_from, valid_to);
```

## Usage Examples

### Example 1: Update Patient Address
```python
from utils.scd2_handler import update_patient_scd2
from datetime import datetime

result = update_patient_scd2(
    patient_id="abc-123-def",
    changes={
        'address':  '123 New Street',
        'city':     'Boston',
        'state':    'MA',
        'zip_code': '02101'
    },
    effective_date=datetime(2025, 6, 15)
)

print(result)
# {'success': True, 'message': 'Created version 2', 'new_patient_key': 1042}
```

### Example 2: Query Current Patient Data
```sql
-- Get current address for all patients
SELECT patient_id, address, city, state
FROM dim_patients
WHERE is_current = TRUE;
```

### Example 3: Point-in-Time Query
```sql
-- What was the patient's address on March 1, 2025?
SELECT address, city, state
FROM dim_patients
WHERE patient_id = 'abc-123-def'
  AND valid_from <= '2025-03-01'
  AND valid_to > '2025-03-01';
```

### Example 4: See Complete Change History
```sql
-- All versions of a patient record
SELECT
    record_version,
    address,
    city,
    state,
    valid_from,
    valid_to,
    is_current
FROM dim_patients
WHERE patient_id = 'abc-123-def'
ORDER BY record_version;
```

## Best Practices

### 1. Always Use Business Keys in Queries

❌ **Wrong:**
```sql
-- Don't join on surrogate key for historical queries
SELECT * FROM fact_encounters e
JOIN dim_patients p ON e.patient_key = p.patient_key
WHERE p.is_current = TRUE;
```

✓ **Correct:**
```sql
-- Join on business key + temporal range
SELECT * FROM fact_encounters e
JOIN dim_patients p
  ON e.patient_id = p.patient_id
  AND e.admission_date BETWEEN p.valid_from AND p.valid_to;
```

### 2. Set Effective Dates Appropriately
```python
# If you know when the change occurred, use that date
update_patient_scd2(
    patient_id="abc-123",
    changes={'insurance_type': 'Medicare'},
    effective_date=datetime(2025, 1, 1)  # Change effective Jan 1
)

# If you don't know, use current time (default)
update_patient_scd2(
    patient_id="abc-123",
    changes={'phone_number': '555-0123'}
    # effective_date defaults to datetime.now()
)
```

### 3. Handle No-Change Updates

The SCD2 handler includes a no-op guard:
```python
# This will NOT create a new version (no actual changes)
result = update_patient_scd2(
    patient_id="abc-123",
    changes={'address': '123 Same Street'}  # Already the current address
)
# Returns: {'success': True, 'message': 'No changes needed'}
```

## Common Queries

### Who changed insurance in the last 90 days?
```sql
SELECT
    p2.patient_id,
    p1.insurance_type as old_insurance,
    p2.insurance_type as new_insurance,
    p2.valid_from as change_date
FROM dim_patients p1
JOIN dim_patients p2
    ON p1.patient_id = p2.patient_id
    AND p2.record_version = p1.record_version + 1
WHERE p1.insurance_type != p2.insurance_type
  AND p2.valid_from > CURRENT_DATE - INTERVAL '90 days'
ORDER BY p2.valid_from DESC;
```

### How many versions does each patient have?
```sql
SELECT
    patient_id,
    COUNT(*) as version_count,
    MAX(record_version) as latest_version,
    MIN(valid_from) as first_seen,
    MAX(CASE WHEN is_current THEN valid_from END) as current_since
FROM dim_patients
GROUP BY patient_id
HAVING COUNT(*) > 1
ORDER BY version_count DESC;
```

## Performance Considerations

- ✓ Index on `(patient_id, is_current)` makes current lookups fast
- ✓ Index on `(valid_from, valid_to)` enables efficient point-in-time queries
- ✓ Partitioning by `valid_from` can improve performance for large tables
- ✓ Regular VACUUM ANALYZE maintains index efficiency

## Limitations

- Storage overhead: Multiple versions consume more space
- Query complexity: Point-in-time joins are more complex than simple joins
- Update latency: Two operations (expire + insert) vs. one (update)

For this healthcare analytics platform, these tradeoffs are acceptable given the value of historical tracking.
