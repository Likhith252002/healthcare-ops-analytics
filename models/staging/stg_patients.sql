-- Staging layer: Clean raw patient data
-- Source: dim_patients
-- Transformations: Type casting, naming conventions, current records only

WITH source AS (
    SELECT * FROM {{ source('public', 'dim_patients') }}
    WHERE is_current = TRUE
),

renamed AS (
    SELECT
        -- IDs
        patient_key,
        patient_id,

        -- Demographics
        first_name,
        last_name,
        CONCAT(first_name, ' ', last_name) AS full_name,
        date_of_birth,
        EXTRACT(YEAR FROM AGE(date_of_birth)) AS age,
        CASE
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) < 18 THEN 'Pediatric'
            WHEN EXTRACT(YEAR FROM AGE(date_of_birth)) BETWEEN 18 AND 64 THEN 'Adult'
            ELSE 'Senior'
        END AS age_group,
        gender,

        -- Contact
        address,
        city,
        state,
        zip_code,
        phone_number,

        -- Insurance
        insurance_type,
        CASE insurance_type
            WHEN 'Private Insurance' THEN 'Commercial'
            WHEN 'Medicare'          THEN 'Government'
            WHEN 'Medicaid'          THEN 'Government'
            WHEN 'Self-Pay/Uninsured' THEN 'Self-Pay'
        END AS insurance_category,

        -- Metadata
        created_at,
        updated_at,
        record_version

    FROM source
)

SELECT * FROM renamed;
