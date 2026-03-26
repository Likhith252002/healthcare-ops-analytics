-- Staging layer: Clean encounter data
-- Source: fact_encounters
-- Transformations: Calculate derived fields, categorize encounters

WITH source AS (
    SELECT * FROM {{ source('public', 'fact_encounters') }}
),

renamed AS (
    SELECT
        -- IDs
        encounter_key,
        patient_key,
        department_key,
        physician_key,
        encounter_id,

        -- Dates
        admission_date,
        discharge_date,
        DATE(admission_date) AS admission_date_only,
        DATE(discharge_date) AS discharge_date_only,

        -- Length of stay
        EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 AS length_of_stay_days,
        CASE
            WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 < 1
                THEN 'Short (0-1 day)'
            WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 BETWEEN 1 AND 3
                THEN 'Medium (1-3 days)'
            WHEN EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400 BETWEEN 3 AND 7
                THEN 'Extended (3-7 days)'
            ELSE 'Long (7+ days)'
        END AS length_of_stay_category,

        -- Encounter details
        admission_type,
        chief_complaint,
        discharge_disposition,

        -- Time categorization
        EXTRACT(DOW FROM admission_date) AS admission_day_of_week,
        CASE EXTRACT(DOW FROM admission_date)
            WHEN 0 THEN 'Sunday'
            WHEN 1 THEN 'Monday'
            WHEN 2 THEN 'Tuesday'
            WHEN 3 THEN 'Wednesday'
            WHEN 4 THEN 'Thursday'
            WHEN 5 THEN 'Friday'
            WHEN 6 THEN 'Saturday'
        END AS admission_day_name,
        CASE
            WHEN EXTRACT(DOW FROM admission_date) IN (0, 6) THEN 'Weekend'
            ELSE 'Weekday'
        END AS admission_weekday_flag,

        -- Metadata
        created_at

    FROM source
)

SELECT * FROM renamed;
