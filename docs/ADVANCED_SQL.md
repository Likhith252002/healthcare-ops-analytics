# Advanced SQL Patterns Guide

## Overview

This guide documents sophisticated SQL techniques used in the healthcare analytics platform. These patterns are essential for complex analytical queries beyond basic JOINs and GROUP BY operations.

## Window Functions

### What Are Window Functions?

Window functions perform calculations across rows related to the current row, without collapsing the result set like GROUP BY does.

**Syntax:**
```sql
function_name() OVER (
    [PARTITION BY column]
    [ORDER BY column]
    [ROWS/RANGE frame_specification]
)
```

### Common Window Functions

#### 1. Ranking Functions

**RANK()** - Assigns rank with gaps for ties
```sql
SELECT
    department_name,
    avg_los,
    RANK() OVER (ORDER BY avg_los) AS rank
FROM dept_metrics;
```

**DENSE_RANK()** - Assigns rank without gaps
**ROW_NUMBER()** - Unique sequential number
**NTILE(n)** - Divides rows into n buckets

#### 2. Offset Functions

**LEAD()** - Access next row value
```sql
-- Find next admission for same patient
LEAD(admission_date) OVER (
    PARTITION BY patient_key
    ORDER BY admission_date
) AS next_admission
```

**LAG()** - Access previous row value
```sql
-- Calculate day-over-day change
daily_count - LAG(daily_count, 1) OVER (ORDER BY date) AS change
```

#### 3. Aggregate Window Functions

**SUM() OVER** - Running totals
```sql
-- Cumulative admissions
SUM(daily_count) OVER (
    ORDER BY date
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
) AS cumulative_total
```

**AVG() OVER** - Moving averages
```sql
-- 7-day moving average
AVG(daily_count) OVER (
    ORDER BY date
    ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
) AS moving_avg_7day
```

### Window Frames

Control which rows are included in the window:
```sql
-- Last 7 days including current
ROWS BETWEEN 6 PRECEDING AND CURRENT ROW

-- All previous rows
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW

-- 3 days before and after
ROWS BETWEEN 3 PRECEDING AND 3 FOLLOWING

-- Based on value range
RANGE BETWEEN INTERVAL '7 days' PRECEDING AND CURRENT ROW
```

## Recursive CTEs

### Use Cases

- Hierarchical data traversal
- Graph analysis
- Timeline reconstruction
- Sequential state tracking

### Syntax
```sql
WITH RECURSIVE cte_name AS (
    -- Base case (non-recursive)
    SELECT ... WHERE initial_condition

    UNION ALL

    -- Recursive case
    SELECT ... FROM cte_name WHERE termination_condition
)
SELECT * FROM cte_name;
```

### Example: Bed Occupancy Timeline
```sql
WITH RECURSIVE bed_timeline AS (
    -- Base: First event
    SELECT bed_number, event_timestamp, 1 AS level
    FROM bed_events
    WHERE event_timestamp = (SELECT MIN(event_timestamp) FROM bed_events)

    UNION ALL

    -- Recursive: Next events
    SELECT e.bed_number, e.event_timestamp, bt.level + 1
    FROM bed_events e
    JOIN bed_timeline bt ON e.bed_number = bt.bed_number
    WHERE e.event_timestamp > bt.event_timestamp
)
SELECT * FROM bed_timeline;
```

**Important:** Always include termination condition to prevent infinite loops!

## Cohort Analysis Pattern

Track groups of entities over time.

### Standard Structure
```sql
-- Step 1: Define cohorts
WITH cohorts AS (
    SELECT
        entity_key,
        DATE_TRUNC('month', first_event) AS cohort_month
    FROM events
    GROUP BY entity_key
),

-- Step 2: Track activity by time period
activity AS (
    SELECT
        c.cohort_month,
        DATE_TRUNC('month', e.event_date) AS activity_month,
        EXTRACT(MONTH FROM AGE(
            DATE_TRUNC('month', e.event_date),
            c.cohort_month
        )) AS months_since_cohort,
        COUNT(DISTINCT e.entity_key) AS active_entities
    FROM cohorts c
    JOIN events e ON c.entity_key = e.entity_key
    GROUP BY c.cohort_month, activity_month
)

-- Step 3: Pivot for cohort table
SELECT
    cohort_month,
    SUM(CASE WHEN months_since_cohort = 0 THEN active_entities END) AS month_0,
    SUM(CASE WHEN months_since_cohort = 1 THEN active_entities END) AS month_1,
    SUM(CASE WHEN months_since_cohort = 2 THEN active_entities END) AS month_2
FROM activity
GROUP BY cohort_month
ORDER BY cohort_month;
```

### Calculating Retention Rates
```sql
ROUND(
    month_1_count::numeric / NULLIF(month_0_count, 0) * 100,
    2
) AS month_1_retention_pct
```

## Performance Optimization for Advanced Queries

### 1. Window Function Optimization

- **Partition wisely:** Smaller partitions = faster
- **Order by indexed columns:** Leverages indexes
- **Limit window frame:** Smaller frames compute faster

### 2. Recursive CTE Performance

- **Set max recursion limit:** Prevent runaway queries
```sql
SET max_recursion_depth = 100;
```

- **Index join columns:** Speed up recursive joins
- **Filter early:** Add WHERE conditions in base case

### 3. Cohort Analysis at Scale

- **Pre-aggregate:** Create summary tables for large cohorts
- **Limit time window:** Don't analyze all history
- **Materialize cohort definitions:** Cache cohort assignments

## Common Pitfalls

### ❌ Avoid: Window function in WHERE
```sql
-- WRONG: Can't filter on window function
SELECT *, RANK() OVER (ORDER BY score) AS rank
FROM table
WHERE rank <= 10;  -- ERROR!
```

✅ **Correct: Use subquery or CTE**
```sql
WITH ranked AS (
    SELECT *, RANK() OVER (ORDER BY score) AS rank
    FROM table
)
SELECT * FROM ranked WHERE rank <= 10;
```

### ❌ Avoid: Unbounded recursive CTE
```sql
-- DANGEROUS: No termination condition!
WITH RECURSIVE infinite AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM infinite  -- Will run forever!
)
SELECT * FROM infinite;
```

✅ **Correct: Add limit**
```sql
WITH RECURSIVE limited AS (
    SELECT 1 AS n
    UNION ALL
    SELECT n + 1 FROM limited WHERE n < 100  -- Stops at 100
)
SELECT * FROM limited;
```

## Real-World Applications

### Healthcare Analytics

- **Readmission tracking:** LEAD() to find subsequent admissions
- **Length of stay trends:** Moving averages over time
- **Patient journey:** Recursive CTEs for care pathways
- **Provider benchmarking:** Percentile ranks for performance

### General Business

- **Customer retention:** Cohort analysis by signup month
- **Sales trends:** Running totals and YoY comparisons
- **Inventory turnover:** FIFO/LIFO using window functions
- **Organizational hierarchy:** Recursive CTEs for reporting chains
