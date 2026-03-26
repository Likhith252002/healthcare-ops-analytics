-- Advanced Analytics Queries
-- Demonstrates: Window functions, ranking, running totals, cohort analysis, recursive CTEs

-- ============================================================================
-- QUERY 1: Patient Readmission Analysis (30-day readmissions)
-- ============================================================================
-- Identifies patients readmitted within 30 days of discharge

WITH encounters_with_next AS (
    SELECT
        encounter_key,
        patient_key,
        admission_date,
        discharge_date,
        admission_type,
        LEAD(admission_date) OVER (
            PARTITION BY patient_key
            ORDER BY admission_date
        ) AS next_admission_date,
        LEAD(encounter_key) OVER (
            PARTITION BY patient_key
            ORDER BY admission_date
        ) AS next_encounter_key
    FROM fact_encounters
),

readmissions AS (
    SELECT
        patient_key,
        encounter_key          AS initial_encounter,
        discharge_date         AS initial_discharge,
        next_encounter_key     AS readmission_encounter,
        next_admission_date    AS readmission_date,
        next_admission_date - discharge_date AS days_to_readmission
    FROM encounters_with_next
    WHERE next_admission_date IS NOT NULL
      AND next_admission_date - discharge_date <= 30
)

SELECT
    p.patient_id,
    p.first_name || ' ' || p.last_name AS patient_name,
    r.initial_discharge,
    r.readmission_date,
    r.days_to_readmission,
    d.department_name
FROM readmissions r
JOIN dim_patients p    ON r.patient_key          = p.patient_key AND p.is_current = TRUE
JOIN fact_encounters e ON r.readmission_encounter = e.encounter_key
JOIN dim_departments d ON e.department_key        = d.department_key
ORDER BY r.days_to_readmission;

-- ============================================================================
-- QUERY 2: Department Performance Ranking (with percentile ranks)
-- ============================================================================
-- Ranks departments by average length of stay with percentile scores

WITH dept_metrics AS (
    SELECT
        d.department_name,
        COUNT(*) AS total_encounters,
        AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400) AS avg_los,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400
        ) AS median_los,
        STDDEV(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400) AS stddev_los
    FROM fact_encounters e
    JOIN dim_departments d ON e.department_key = d.department_key
    GROUP BY d.department_name
)

SELECT
    department_name,
    total_encounters,
    ROUND(avg_los::numeric, 2)    AS avg_length_of_stay_days,
    ROUND(median_los::numeric, 2) AS median_length_of_stay_days,
    ROUND(stddev_los::numeric, 2) AS stddev_length_of_stay,
    RANK()         OVER (ORDER BY avg_los)       AS los_rank,
    PERCENT_RANK() OVER (ORDER BY avg_los)       AS los_percentile,
    NTILE(4)       OVER (ORDER BY avg_los)       AS los_quartile,
    CASE
        WHEN PERCENT_RANK() OVER (ORDER BY avg_los) < 0.25 THEN 'Top Performer'
        WHEN PERCENT_RANK() OVER (ORDER BY avg_los) < 0.75 THEN 'Average'
        ELSE 'Needs Improvement'
    END AS performance_category
FROM dept_metrics
ORDER BY avg_los;

-- ============================================================================
-- QUERY 3: Running Totals and Moving Averages (Daily Admissions)
-- ============================================================================
-- Shows daily admission counts with 7-day moving average

WITH daily_admissions AS (
    SELECT
        DATE(admission_date) AS admission_date,
        COUNT(*)             AS daily_count
    FROM fact_encounters
    GROUP BY DATE(admission_date)
)

SELECT
    admission_date,
    daily_count,
    SUM(daily_count) OVER (
        ORDER BY admission_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_admissions,
    AVG(daily_count) OVER (
        ORDER BY admission_date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS moving_avg_7day,
    daily_count - LAG(daily_count, 1) OVER (ORDER BY admission_date) AS day_over_day_change,
    ROUND(
        (daily_count::numeric - LAG(daily_count, 1) OVER (ORDER BY admission_date))
        / NULLIF(LAG(daily_count, 1) OVER (ORDER BY admission_date), 0) * 100,
        2
    ) AS day_over_day_pct_change
FROM daily_admissions
ORDER BY admission_date DESC
LIMIT 30;

-- ============================================================================
-- QUERY 4: Cohort Analysis (Patient First Visit Month)
-- ============================================================================
-- Analyzes patient retention by first visit cohort

WITH patient_first_visit AS (
    SELECT
        patient_key,
        MIN(DATE_TRUNC('month', admission_date)) AS cohort_month,
        MIN(admission_date)                       AS first_visit_date
    FROM fact_encounters
    GROUP BY patient_key
),

patient_visits_by_month AS (
    SELECT
        pf.patient_key,
        pf.cohort_month,
        DATE_TRUNC('month', e.admission_date) AS visit_month,
        EXTRACT(MONTH FROM AGE(
            DATE_TRUNC('month', e.admission_date),
            pf.cohort_month
        )) AS months_since_first
    FROM patient_first_visit pf
    JOIN fact_encounters e ON pf.patient_key = e.patient_key
)

SELECT
    cohort_month,
    COUNT(DISTINCT CASE WHEN months_since_first = 0 THEN patient_key END) AS month_0_patients,
    COUNT(DISTINCT CASE WHEN months_since_first = 1 THEN patient_key END) AS month_1_patients,
    COUNT(DISTINCT CASE WHEN months_since_first = 2 THEN patient_key END) AS month_2_patients,
    COUNT(DISTINCT CASE WHEN months_since_first = 3 THEN patient_key END) AS month_3_patients,
    ROUND(
        COUNT(DISTINCT CASE WHEN months_since_first = 1 THEN patient_key END)::numeric
        / NULLIF(COUNT(DISTINCT CASE WHEN months_since_first = 0 THEN patient_key END), 0) * 100,
        2
    ) AS month_1_retention_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN months_since_first = 2 THEN patient_key END)::numeric
        / NULLIF(COUNT(DISTINCT CASE WHEN months_since_first = 0 THEN patient_key END), 0) * 100,
        2
    ) AS month_2_retention_pct,
    ROUND(
        COUNT(DISTINCT CASE WHEN months_since_first = 3 THEN patient_key END)::numeric
        / NULLIF(COUNT(DISTINCT CASE WHEN months_since_first = 0 THEN patient_key END), 0) * 100,
        2
    ) AS month_3_retention_pct
FROM patient_visits_by_month
GROUP BY cohort_month
ORDER BY cohort_month DESC
LIMIT 12;

-- ============================================================================
-- QUERY 5: Physician Utilization and Efficiency
-- ============================================================================
-- Analyzes physician workload with patient distribution

WITH physician_stats AS (
    SELECT
        ph.physician_key,
        ph.first_name || ' ' || ph.last_name AS physician_name,
        ph.specialty,
        d.department_name,
        COUNT(DISTINCT e.encounter_key)        AS total_encounters,
        COUNT(DISTINCT e.patient_key)          AS unique_patients,
        AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400) AS avg_los,
        COUNT(DISTINCT DATE(e.admission_date)) AS active_days
    FROM dim_physicians ph
    JOIN fact_encounters e ON ph.physician_key    = e.physician_key
    JOIN dim_departments d ON ph.department_key   = d.department_key
    GROUP BY ph.physician_key, ph.first_name, ph.last_name, ph.specialty, d.department_name
)

SELECT
    physician_name,
    specialty,
    department_name,
    total_encounters,
    unique_patients,
    ROUND(total_encounters::numeric / unique_patients, 2)              AS encounters_per_patient,
    ROUND(avg_los::numeric, 2)                                         AS avg_length_of_stay,
    active_days,
    ROUND(total_encounters::numeric / NULLIF(active_days, 0), 2)      AS encounters_per_active_day,
    PERCENT_RANK() OVER (
        PARTITION BY specialty ORDER BY total_encounters
    ) AS workload_percentile_in_specialty,
    CASE
        WHEN total_encounters > AVG(total_encounters) OVER (PARTITION BY specialty) * 1.5
            THEN 'High Utilization'
        WHEN total_encounters > AVG(total_encounters) OVER (PARTITION BY specialty) * 0.5
            THEN 'Normal Utilization'
        ELSE 'Low Utilization'
    END AS utilization_category
FROM physician_stats
ORDER BY total_encounters DESC;

-- ============================================================================
-- QUERY 6: Recursive CTE - Bed Occupancy Timeline
-- ============================================================================
-- Generates timeline of bed occupancy changes

WITH RECURSIVE bed_timeline AS (
    -- Base case: earliest bed event per bed
    SELECT
        department_key,
        bed_number,
        event_timestamp,
        event_type,
        1 AS occupancy_level,
        encounter_key
    FROM fact_bed_events
    WHERE event_timestamp = (
        SELECT MIN(event_timestamp)
        FROM fact_bed_events be2
        WHERE be2.department_key = fact_bed_events.department_key
          AND be2.bed_number     = fact_bed_events.bed_number
    )

    UNION ALL

    -- Recursive case: next event for same bed
    SELECT
        fbe.department_key,
        fbe.bed_number,
        fbe.event_timestamp,
        fbe.event_type,
        CASE
            WHEN fbe.event_type = 'bed_assigned'   THEN bt.occupancy_level + 1
            WHEN fbe.event_type = 'bed_discharged' THEN bt.occupancy_level - 1
            ELSE bt.occupancy_level
        END,
        fbe.encounter_key
    FROM fact_bed_events fbe
    JOIN bed_timeline bt
        ON  fbe.department_key  = bt.department_key
        AND fbe.bed_number      = bt.bed_number
        AND fbe.event_timestamp > bt.event_timestamp
    WHERE fbe.event_timestamp = (
        SELECT MIN(event_timestamp)
        FROM fact_bed_events be3
        WHERE be3.department_key  = bt.department_key
          AND be3.bed_number      = bt.bed_number
          AND be3.event_timestamp > bt.event_timestamp
    )
)

SELECT
    d.department_name,
    bt.bed_number,
    bt.event_timestamp,
    bt.event_type,
    bt.occupancy_level,
    CASE WHEN bt.occupancy_level > 0 THEN 'Occupied' ELSE 'Available' END AS bed_status
FROM bed_timeline bt
JOIN dim_departments d ON bt.department_key = d.department_key
ORDER BY bt.department_key, bt.bed_number, bt.event_timestamp
LIMIT 100;
