-- Dashboard Metrics Layer
-- Pre-aggregated tables for visualization tools
-- Optimized for fast querying in BI dashboards

-- ============================================================================
-- METRIC 1: Daily Hospital Snapshot
-- ============================================================================
-- One row per day with key hospital-wide metrics

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_daily_hospital_snapshot AS
WITH daily_encounters AS (
    SELECT
        DATE(admission_date)                                                 AS metric_date,
        COUNT(*)                                                             AS admissions,
        COUNT(DISTINCT patient_key)                                          AS unique_patients,
        AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400)  AS avg_los_days,
        COUNT(CASE WHEN admission_type = 'Emergency' THEN 1 END)            AS emergency_admissions,
        COUNT(CASE WHEN admission_type = 'Scheduled' THEN 1 END)            AS scheduled_admissions
    FROM fact_encounters
    GROUP BY DATE(admission_date)
),

daily_beds AS (
    SELECT
        DATE(event_timestamp)                                                    AS metric_date,
        COUNT(DISTINCT CASE WHEN event_type = 'bed_assigned'   THEN bed_number END) AS beds_assigned,
        COUNT(DISTINCT CASE WHEN event_type = 'bed_discharged' THEN bed_number END) AS beds_released
    FROM fact_bed_events
    GROUP BY DATE(event_timestamp)
),

combined AS (
    SELECT
        COALESCE(e.metric_date, b.metric_date)                 AS metric_date,
        COALESCE(e.admissions, 0)                              AS total_admissions,
        COALESCE(e.unique_patients, 0)                         AS unique_patients,
        ROUND(COALESCE(e.avg_los_days, 0)::numeric, 2)        AS avg_length_of_stay,
        COALESCE(e.emergency_admissions, 0)                    AS emergency_admissions,
        COALESCE(e.scheduled_admissions, 0)                    AS scheduled_admissions,
        COALESCE(b.beds_assigned, 0)                           AS beds_assigned,
        COALESCE(b.beds_released, 0)                           AS beds_released,
        ROUND(
            COALESCE(e.emergency_admissions, 0)::numeric /
            NULLIF(COALESCE(e.admissions, 0), 0) * 100,
            2
        )                                                      AS emergency_pct,
        EXTRACT(DOW FROM COALESCE(e.metric_date, b.metric_date)) AS day_of_week,
        CASE
            WHEN EXTRACT(DOW FROM COALESCE(e.metric_date, b.metric_date)) IN (0, 6)
                THEN 'Weekend'
            ELSE 'Weekday'
        END                                                    AS weekday_flag
    FROM daily_encounters e
    FULL OUTER JOIN daily_beds b ON e.metric_date = b.metric_date
)

SELECT * FROM combined
ORDER BY metric_date DESC;

CREATE INDEX IF NOT EXISTS idx_daily_snapshot_date ON mv_daily_hospital_snapshot(metric_date);

-- ============================================================================
-- METRIC 2: Department Performance Dashboard
-- ============================================================================
-- Current metrics by department for KPI cards

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_department_performance AS
WITH dept_encounters AS (
    SELECT
        d.department_key,
        d.department_name,
        d.bed_capacity,
        COUNT(e.encounter_key)                                                           AS total_encounters,
        COUNT(DISTINCT e.patient_key)                                                    AS unique_patients,
        AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)          AS avg_los_days,
        PERCENTILE_CONT(0.5) WITHIN GROUP (
            ORDER BY EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400
        )                                                                                AS median_los_days,
        COUNT(CASE WHEN e.admission_type = 'Emergency' THEN 1 END)                      AS emergency_count,
        COUNT(CASE WHEN e.discharge_date IS NOT NULL   THEN 1 END)                      AS discharged_count
    FROM dim_departments d
    LEFT JOIN fact_encounters e ON d.department_key = e.department_key
    GROUP BY d.department_key, d.department_name, d.bed_capacity
),

dept_beds AS (
    SELECT
        department_key,
        COUNT(DISTINCT bed_number) AS unique_beds_used,
        MAX(bed_number)            AS max_bed_number_used
    FROM fact_bed_events
    GROUP BY department_key
),

dept_physicians AS (
    SELECT
        department_key,
        COUNT(*) AS physician_count
    FROM dim_physicians
    GROUP BY department_key
)

SELECT
    de.department_key,
    de.department_name,
    de.bed_capacity,
    COALESCE(dp.physician_count, 0)                                        AS physician_count,
    de.total_encounters,
    de.unique_patients,
    ROUND(de.avg_los_days::numeric,    2)                                  AS avg_length_of_stay,
    ROUND(de.median_los_days::numeric, 2)                                  AS median_length_of_stay,
    de.emergency_count,
    de.discharged_count,
    COALESCE(db.unique_beds_used, 0)                                       AS unique_beds_used,
    ROUND(
        COALESCE(db.unique_beds_used, 0)::numeric /
        NULLIF(de.bed_capacity, 0) * 100,
        2
    )                                                                      AS bed_utilization_pct,
    ROUND(
        de.total_encounters::numeric /
        NULLIF(COALESCE(dp.physician_count, 0), 0),
        2
    )                                                                      AS encounters_per_physician,
    ROUND(
        de.emergency_count::numeric /
        NULLIF(de.total_encounters, 0) * 100,
        2
    )                                                                      AS emergency_pct,
    ROUND(
        de.discharged_count::numeric /
        NULLIF(de.total_encounters, 0) * 100,
        2
    )                                                                      AS discharge_pct
FROM dept_encounters de
LEFT JOIN dept_beds      db ON de.department_key = db.department_key
LEFT JOIN dept_physicians dp ON de.department_key = dp.department_key
ORDER BY de.total_encounters DESC;

-- ============================================================================
-- METRIC 3: Patient Demographics Summary
-- ============================================================================
-- Distribution metrics for patient population

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_patient_demographics AS
WITH patient_stats AS (
    SELECT
        CASE
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 18             THEN '0-17 (Pediatric)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 18 AND 34 THEN '18-34 (Young Adult)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 35 AND 54 THEN '35-54 (Middle Age)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 55 AND 74 THEN '55-74 (Senior)'
            ELSE '75+ (Elderly)'
        END    AS age_group,
        gender,
        insurance_type,
        state,
        COUNT(*) AS patient_count
    FROM dim_patients
    WHERE is_current = TRUE
    GROUP BY
        CASE
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 18             THEN '0-17 (Pediatric)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 18 AND 34 THEN '18-34 (Young Adult)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 35 AND 54 THEN '35-54 (Middle Age)'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 55 AND 74 THEN '55-74 (Senior)'
            ELSE '75+ (Elderly)'
        END,
        gender,
        insurance_type,
        state
)

SELECT
    age_group,
    gender,
    insurance_type,
    state,
    patient_count,
    ROUND(
        patient_count::numeric /
        SUM(patient_count) OVER () * 100,
        2
    ) AS pct_of_total_patients,
    ROUND(
        patient_count::numeric /
        SUM(patient_count) OVER (PARTITION BY age_group) * 100,
        2
    ) AS pct_within_age_group
FROM patient_stats
ORDER BY age_group, patient_count DESC;

-- ============================================================================
-- METRIC 4: Time Series - Weekly Trends
-- ============================================================================
-- Weekly aggregations for trend charts

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_weekly_trends AS
WITH weekly_data AS (
    SELECT
        DATE_TRUNC('week', admission_date)                                          AS week_start,
        DATE_TRUNC('week', admission_date) + INTERVAL '6 days'                     AS week_end,
        COUNT(*)                                                                    AS weekly_admissions,
        COUNT(DISTINCT patient_key)                                                 AS unique_patients,
        AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400)         AS avg_los,
        COUNT(CASE WHEN admission_type = 'Emergency' THEN 1 END)                   AS emergency_admissions,
        COUNT(CASE WHEN admission_type = 'Scheduled' THEN 1 END)                   AS scheduled_admissions
    FROM fact_encounters
    GROUP BY DATE_TRUNC('week', admission_date)
)

SELECT
    week_start,
    week_end,
    weekly_admissions,
    unique_patients,
    ROUND(avg_los::numeric, 2)                                                     AS avg_length_of_stay,
    emergency_admissions,
    scheduled_admissions,
    ROUND(
        emergency_admissions::numeric /
        NULLIF(weekly_admissions, 0) * 100,
        2
    )                                                                              AS emergency_pct,
    weekly_admissions - LAG(weekly_admissions, 1) OVER (ORDER BY week_start)      AS wow_admissions_change,
    ROUND(
        (weekly_admissions - LAG(weekly_admissions, 1) OVER (ORDER BY week_start))::numeric /
        NULLIF(LAG(weekly_admissions, 1) OVER (ORDER BY week_start), 0) * 100,
        2
    )                                                                              AS wow_admissions_pct_change
FROM weekly_data
ORDER BY week_start DESC;

CREATE INDEX IF NOT EXISTS idx_weekly_trends_date ON mv_weekly_trends(week_start);

-- ============================================================================
-- METRIC 5: Top Chief Complaints
-- ============================================================================
-- Most common reasons for admission

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_top_complaints AS
SELECT
    chief_complaint,
    COUNT(*)                                                         AS encounter_count,
    COUNT(DISTINCT patient_key)                                      AS unique_patients,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400)::numeric,
        2
    )                                                                AS avg_los_days,
    COUNT(CASE WHEN admission_type = 'Emergency' THEN 1 END)        AS emergency_count,
    ROUND(
        COUNT(*)::numeric /
        SUM(COUNT(*)) OVER () * 100,
        2
    )                                                                AS pct_of_total_encounters,
    RANK() OVER (ORDER BY COUNT(*) DESC)                             AS complaint_rank
FROM fact_encounters
GROUP BY chief_complaint
ORDER BY encounter_count DESC
LIMIT 20;
