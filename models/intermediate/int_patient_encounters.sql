-- Intermediate layer: Patient-encounter enriched dataset
-- Combines staging tables for analysis
-- One row per encounter with patient demographics

WITH patients AS (
    SELECT * FROM {{ ref('stg_patients') }}
),

encounters AS (
    SELECT * FROM {{ ref('stg_encounters') }}
),

departments AS (
    SELECT * FROM {{ source('public', 'dim_departments') }}
),

physicians AS (
    SELECT * FROM {{ source('public', 'dim_physicians') }}
),

joined AS (
    SELECT
        -- Encounter info
        e.encounter_key,
        e.encounter_id,
        e.admission_date,
        e.discharge_date,
        e.length_of_stay_days,
        e.length_of_stay_category,
        e.admission_type,
        e.chief_complaint,
        e.discharge_disposition,
        e.admission_day_name,
        e.admission_weekday_flag,

        -- Patient demographics
        p.patient_key,
        p.patient_id,
        p.full_name          AS patient_name,
        p.age                AS patient_age,
        p.age_group          AS patient_age_group,
        p.gender             AS patient_gender,
        p.insurance_type,
        p.insurance_category,
        p.city               AS patient_city,
        p.state              AS patient_state,

        -- Department
        d.department_key,
        d.department_name,
        d.department_type,

        -- Physician
        ph.physician_key,
        ph.first_name || ' ' || ph.last_name AS physician_name,
        ph.specialty                          AS physician_specialty

    FROM encounters e
    INNER JOIN patients    p  ON e.patient_key    = p.patient_key
    INNER JOIN departments d  ON e.department_key = d.department_key
    INNER JOIN physicians  ph ON e.physician_key  = ph.physician_key
)

SELECT * FROM joined;
