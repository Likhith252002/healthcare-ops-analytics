# Performance Optimization Guide

## Current Performance Metrics

Based on benchmarks with 16,000+ records:

| Operation | Avg Time | Notes |
|-----------|----------|-------|
| Current patient lookup (indexed) | <5ms | Using `is_current` index |
| ER encounter count | 15-25ms | Join + filter on 5K records |
| Bed utilization (7 days) | 10-20ms | Time-range filter optimized |
| Point-in-time patient query | <10ms | Using valid_from/valid_to index |

## Indexing Strategy

### Implemented Indexes
```sql
-- Primary keys (auto-indexed)
patient_key, department_key, physician_key, encounter_key, bed_event_key

-- Foreign key indexes (explicit)
CREATE INDEX idx_encounters_patient_key ON fact_encounters(patient_key);
CREATE INDEX idx_encounters_department_key ON fact_encounters(department_key);
CREATE INDEX idx_bed_events_encounter_key ON fact_bed_events(encounter_key);

-- Date/time indexes (for range queries)
CREATE INDEX idx_encounters_admission_date ON fact_encounters(admission_date);
CREATE INDEX idx_bed_events_timestamp ON fact_bed_events(event_timestamp);

-- SCD2 indexes
CREATE INDEX idx_patients_business_key_current ON dim_patients(patient_id, is_current);
CREATE INDEX idx_patients_valid_dates ON dim_patients(valid_from, valid_to);
```

### Index Usage Guidelines

**✓ Create indexes for:**
- Foreign keys (JOIN columns)
- Date/time columns (WHERE filters, ORDER BY)
- Boolean flags + business keys (composite indexes)
- Columns in GROUP BY or DISTINCT queries

**✗ Avoid indexes for:**
- Low-cardinality columns (gender, admission_type)
- Columns rarely used in queries
- Very small tables (<1000 rows)

## Query Optimization Patterns

### Pattern 1: Use Covering Indexes
```sql
-- Instead of SELECT *
SELECT patient_id, is_current FROM dim_patients
WHERE is_current = TRUE;

-- Index can satisfy entire query without table lookup
```

### Pattern 2: Limit Result Sets Early
```sql
-- Good: Filter early, join later
SELECT e.* FROM (
    SELECT * FROM fact_encounters
    WHERE admission_date > '2025-01-01'
) e
JOIN dim_patients p ON e.patient_key = p.patient_key;

-- Avoid: Join all, filter late
SELECT e.* FROM fact_encounters e
JOIN dim_patients p ON e.patient_key = p.patient_key
WHERE e.admission_date > '2025-01-01';
```

### Pattern 3: Use EXISTS Instead of COUNT
```sql
-- Faster: Stops at first match
SELECT EXISTS(
    SELECT 1 FROM fact_encounters
    WHERE patient_key = 123
);

-- Slower: Counts all matches
SELECT COUNT(*) > 0 FROM fact_encounters
WHERE patient_key = 123;
```

## Batch Processing Optimizations

Current batch sizes (from data generators):
- Patients: 100 records/commit
- Encounters: 100 records/commit
- Bed events: 500 records/commit (higher because simpler records)

**Rule of thumb:** Commit every 100-500 records for good balance between:
- Transaction overhead (fewer commits = faster)
- Memory usage (smaller batches = less RAM)
- Rollback risk (smaller batches = less data lost on error)

## Database Maintenance

### Regular VACUUM
```sql
-- Analyze all tables (update statistics)
VACUUM ANALYZE;

-- Specific table after large data changes
VACUUM ANALYZE dim_patients;
```

Run after:
- Bulk data loads
- Large DELETE operations
- Significant UPDATE operations (like SCD2 updates)

### Monitor Table Bloat
```sql
-- Check dead tuples (should VACUUM if high)
SELECT
    schemaname,
    relname,
    n_dead_tup,
    n_live_tup,
    ROUND(n_dead_tup * 100.0 / NULLIF(n_live_tup + n_dead_tup, 0), 2) as dead_pct
FROM pg_stat_user_tables
WHERE n_dead_tup > 0
ORDER BY n_dead_tup DESC;
```

## Scaling Recommendations

Current scale: **~16K records, <100MB total**

| Scale | Records | Recommendations |
|-------|---------|----------------|
| Small | <100K | Current setup is optimal |
| Medium | 100K-1M | Add partitioning on date columns |
| Large | 1M-10M | Consider table partitioning + connection pooling |
| Enterprise | >10M | Separate OLTP/OLAP databases, use data warehouse |

## Benchmarking

Run performance tests:
```bash
python src/benchmark_queries.py
```

This reports:
- Query execution times (avg/min/max)
- Table sizes
- Index usage statistics

Re-run after:
- Adding new indexes
- Data volume increases
- Query optimizations
