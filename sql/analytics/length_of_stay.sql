-- Length of Stay Analysis
-- Average stay duration by department and admission type

SELECT
    d.department_name,
    e.admission_type,
    COUNT(*) as num_encounters,
    ROUND(AVG(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 2) as avg_los_days,
    ROUND(MIN(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 2) as min_los_days,
    ROUND(MAX(EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 2) as max_los_days,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (e.discharge_date - e.admission_date)) / 86400)::numeric, 2) as median_los_days
FROM fact_encounters e
JOIN dim_departments d ON e.department_key = d.department_key
GROUP BY d.department_name, e.admission_type
ORDER BY d.department_name, e.admission_type;
