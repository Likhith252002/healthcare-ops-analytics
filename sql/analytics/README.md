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

## Testing Queries

After running the data generation pipeline, test these queries:
```bash
# Test all queries
for file in sql/analytics/*.sql; do
    echo "Running $file..."
    psql -d healthcare_ops -f "$file" | head -20
done
```
