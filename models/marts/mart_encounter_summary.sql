-- Mart layer: Encounter summary for business reporting
-- Aggregates key metrics by various dimensions

WITH base AS (
    SELECT * FROM {{ ref('int_patient_encounters') }}
),

summary AS (
    SELECT
        -- Time dimensions
        DATE_TRUNC('day',   admission_date) AS encounter_date,
        DATE_TRUNC('week',  admission_date) AS encounter_week,
        DATE_TRUNC('month', admission_date) AS encounter_month,

        -- Categorical dimensions
        department_name,
        admission_type,
        patient_age_group,
        insurance_category,
        admission_weekday_flag,

        -- Metrics
        COUNT(*)                                                               AS encounter_count,
        COUNT(DISTINCT patient_key)                                            AS unique_patients,
        AVG(length_of_stay_days)                                               AS avg_length_of_stay,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY length_of_stay_days)       AS median_length_of_stay,
        MIN(length_of_stay_days)                                               AS min_length_of_stay,
        MAX(length_of_stay_days)                                               AS max_length_of_stay,

        -- Counts by admission type
        SUM(CASE WHEN admission_type = 'Emergency' THEN 1 ELSE 0 END)         AS emergency_count,
        SUM(CASE WHEN admission_type = 'Scheduled' THEN 1 ELSE 0 END)         AS scheduled_count,
        SUM(CASE WHEN admission_type = 'Transfer'  THEN 1 ELSE 0 END)         AS transfer_count

    FROM base
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8
)

SELECT * FROM summary
ORDER BY encounter_date DESC, department_name;
