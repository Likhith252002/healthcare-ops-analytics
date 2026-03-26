-- Patient History Analysis
-- Query patient demographics as they existed at specific points in time

-- Example 1: Get current patient demographics
SELECT
    patient_id,
    first_name,
    last_name,
    address,
    city,
    state,
    zip_code,
    insurance_type,
    valid_from,
    valid_to,
    record_version
FROM dim_patients
WHERE is_current = TRUE
ORDER BY last_name, first_name
LIMIT 20;

-- Example 2: Point-in-time query - patients as they existed on a specific date
-- Replace '2025-12-01' with your target date
WITH target_date AS (
    SELECT '2025-12-01'::timestamp as query_date
)
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    p.address,
    p.city,
    p.state,
    p.insurance_type,
    p.valid_from,
    p.valid_to,
    p.record_version
FROM dim_patients p, target_date t
WHERE p.valid_from <= t.query_date
  AND p.valid_to > t.query_date
ORDER BY p.last_name, p.first_name;

-- Example 3: Patient change history - see all versions of a specific patient
-- Replace 'patient-uuid-here' with actual patient_id
SELECT
    patient_key,
    patient_id,
    address,
    city,
    state,
    zip_code,
    insurance_type,
    valid_from,
    valid_to,
    is_current,
    record_version,
    EXTRACT(EPOCH FROM (valid_to - valid_from)) / 86400 as days_active
FROM dim_patients
WHERE patient_id = 'patient-uuid-here'
ORDER BY valid_from DESC;

-- Example 4: Patients who changed insurance type
SELECT
    p1.patient_id,
    p1.first_name || ' ' || p1.last_name as patient_name,
    p1.insurance_type as old_insurance,
    p2.insurance_type as new_insurance,
    p2.valid_from as change_date,
    p1.record_version as old_version,
    p2.record_version as new_version
FROM dim_patients p1
JOIN dim_patients p2
    ON p1.patient_id = p2.patient_id
    AND p2.record_version = p1.record_version + 1
WHERE p1.insurance_type != p2.insurance_type
ORDER BY p2.valid_from DESC;

-- Example 5: Patients who moved (address changed)
SELECT
    p1.patient_id,
    p1.first_name || ' ' || p1.last_name as patient_name,
    p1.city || ', ' || p1.state as old_location,
    p2.city || ', ' || p2.state as new_location,
    p2.valid_from as move_date,
    p2.record_version - p1.record_version as versions_between
FROM dim_patients p1
JOIN dim_patients p2
    ON p1.patient_id = p2.patient_id
    AND p2.record_version = p1.record_version + 1
WHERE (p1.address != p2.address OR p1.city != p2.city OR p1.state != p2.state)
ORDER BY p2.valid_from DESC;
