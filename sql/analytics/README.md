# Analytics Queries

This directory contains SQL queries for calculating operational metrics.

## Available Queries

### 1. ER Wait Times (`er_wait_times.sql`)
Calculates Emergency Department wait time statistics by date and hour.

Metrics:
- Average, min, max wait times
- Median (P50) and P95 wait times
- Encounter volume by hour

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/er_wait_times.sql
```

### 2. Bed Utilization (`bed_utilization.sql`)
Calculates hourly bed occupancy rates for each department.

Metrics:
- Occupied beds vs. capacity
- Occupancy rate percentage
- Time-series tracking

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/bed_utilization.sql
```

### 3. Length of Stay (`length_of_stay.sql`)
Analyzes patient length of stay by department and admission type.

Metrics:
- Average, min, max, median LOS
- Breakdown by admission type (Emergency, Scheduled, Transfer)

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/length_of_stay.sql
```

### 4. Daily Volume (`daily_volume.sql`)
Tracks daily patient volume trends.

Metrics:
- Encounter counts by date and department
- Percentage of daily total
- Admission type distribution

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/daily_volume.sql
```

### 5. Patient History (`patient_history.sql`)
Demonstrates Type 2 SCD capabilities with point-in-time queries.

Queries included:
- Current patient demographics (active records only)
- Point-in-time reconstruction (patients as they existed on date X)
- Complete change history for a patient (all versions)
- Insurance type changes over time
- Address changes (patient moves)

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/patient_history.sql
```

**Point-in-Time Query Example:**
To see patient data as it existed on December 1, 2025:
```sql
-- Edit the query_date in the CTE
SELECT ... WHERE valid_from <= '2025-12-01' AND valid_to > '2025-12-01'
```

### 6. Advanced Analytics (`advanced_analytics.sql`)
Expert-level SQL demonstrating sophisticated analytical techniques.

**Queries included:**

1. **30-Day Readmissions** - LEAD() window function to identify patient readmissions
2. **Department Performance Ranking** - RANK(), PERCENT_RANK(), NTILE() for performance tiers
3. **Running Totals & Moving Averages** - SUM() OVER, AVG() OVER with window frames
4. **Cohort Analysis** - Patient retention by first visit month
5. **Physician Utilization** - Workload analysis with partition-based comparisons
6. **Recursive Bed Timeline** - Recursive CTE tracking occupancy state changes

**Techniques demonstrated:**
- Window functions (LEAD, LAG, RANK, NTILE, PERCENT_RANK)
- Window frames (ROWS BETWEEN, UNBOUNDED PRECEDING)
- Recursive CTEs (WITH RECURSIVE)
- Cohort analysis patterns
- Running totals and moving averages
- Percentile calculations

Usage:
```bash
psql -d healthcare_ops -f sql/analytics/advanced_analytics.sql
```

## Testing Queries

After running the data generation pipeline, test these queries:
```bash
# Test all queries
for file in sql/analytics/*.sql; do
    echo "Running $file..."
    psql -d healthcare_ops -f "$file" | head -20
done
```
