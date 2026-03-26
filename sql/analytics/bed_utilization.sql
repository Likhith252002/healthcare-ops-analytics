-- Bed Utilization Analysis
-- Calculates hourly bed occupancy rate by department

WITH hourly_slots AS (
    SELECT
        department_key,
        generate_series(
            DATE_TRUNC('hour', MIN(event_timestamp)),
            DATE_TRUNC('hour', MAX(event_timestamp)),
            INTERVAL '1 hour'
        ) as time_slot
    FROM fact_bed_events
    GROUP BY department_key
),
bed_status AS (
    SELECT
        hs.department_key,
        hs.time_slot,
        COUNT(DISTINCT CASE
            WHEN be_assigned.event_timestamp <= hs.time_slot
            AND (be_discharged.event_timestamp > hs.time_slot OR be_discharged.event_timestamp IS NULL)
            THEN be_assigned.bed_number
        END) as occupied_beds
    FROM hourly_slots hs
    LEFT JOIN fact_bed_events be_assigned
        ON hs.department_key = be_assigned.department_key
        AND be_assigned.event_type = 'bed_assigned'
    LEFT JOIN fact_bed_events be_discharged
        ON be_assigned.encounter_key = be_discharged.encounter_key
        AND be_discharged.event_type = 'bed_discharged'
    GROUP BY hs.department_key, hs.time_slot
)
SELECT
    d.department_name,
    DATE(bs.time_slot) as date,
    EXTRACT(HOUR FROM bs.time_slot) as hour,
    bs.occupied_beds,
    d.bed_capacity,
    ROUND((bs.occupied_beds::numeric / d.bed_capacity * 100), 1) as occupancy_rate_pct
FROM bed_status bs
JOIN dim_departments d ON bs.department_key = d.department_key
WHERE bs.occupied_beds > 0
ORDER BY d.department_name, date DESC, hour;
