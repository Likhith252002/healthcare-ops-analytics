-- Emergency Department Wait Time Analysis
-- Calculates wait time metrics by date and hour

WITH er_encounters AS (
    SELECT
        e.encounter_key,
        e.admission_date,
        e.discharge_date,
        DATE(e.admission_date) as encounter_date,
        EXTRACT(HOUR FROM e.admission_date) as encounter_hour,
        EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 3600 as length_of_stay_hours,
        d.department_name
    FROM fact_encounters e
    JOIN dim_departments d ON e.department_key = d.department_key
    WHERE d.department_name = 'Emergency Department'
)
SELECT
    encounter_date,
    encounter_hour,
    COUNT(*) as num_encounters,
    ROUND(AVG(length_of_stay_hours)::numeric, 2) as avg_wait_hours,
    ROUND(MIN(length_of_stay_hours)::numeric, 2) as min_wait_hours,
    ROUND(MAX(length_of_stay_hours)::numeric, 2) as max_wait_hours,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY length_of_stay_hours)::numeric, 2) as median_wait_hours,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY length_of_stay_hours)::numeric, 2) as p95_wait_hours
FROM er_encounters
GROUP BY encounter_date, encounter_hour
ORDER BY encounter_date DESC, encounter_hour;
