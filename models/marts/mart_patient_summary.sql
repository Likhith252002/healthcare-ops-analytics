-- Mart layer: Patient summary metrics
-- One row per patient with lifetime statistics

WITH base AS (
    SELECT * FROM {{ ref('int_patient_encounters') }}
),

patient_metrics AS (
    SELECT
        -- Patient identifiers
        patient_key,
        patient_id,
        patient_name,
        patient_age,
        patient_age_group,
        patient_gender,
        insurance_type,
        insurance_category,
        patient_city,
        patient_state,

        -- Encounter metrics
        COUNT(*)                        AS total_encounters,
        COUNT(DISTINCT department_key)  AS departments_visited,
        MIN(admission_date)             AS first_encounter_date,
        MAX(admission_date)             AS last_encounter_date,

        -- Length of stay metrics
        SUM(length_of_stay_days)        AS total_days_hospitalized,
        AVG(length_of_stay_days)        AS avg_length_of_stay,
        MAX(length_of_stay_days)        AS max_length_of_stay,

        -- Admission type breakdown
        SUM(CASE WHEN admission_type = 'Emergency' THEN 1 ELSE 0 END) AS emergency_visits,
        SUM(CASE WHEN admission_type = 'Scheduled' THEN 1 ELSE 0 END) AS scheduled_visits,
        SUM(CASE WHEN admission_type = 'Transfer'  THEN 1 ELSE 0 END) AS transfer_visits,

        -- Flags
        CASE WHEN COUNT(*) >= 3                                                           THEN TRUE ELSE FALSE END AS is_frequent_patient,
        CASE WHEN MAX(admission_date) > CURRENT_DATE - INTERVAL '30 days'                THEN TRUE ELSE FALSE END AS recent_visit_30d

    FROM base
    GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10
)

SELECT * FROM patient_metrics
ORDER BY total_encounters DESC;
