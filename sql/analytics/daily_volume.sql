-- Daily Volume Analysis
-- Count of encounters by date, department, and admission type

SELECT
    DATE(e.admission_date) as admission_date,
    d.department_name,
    e.admission_type,
    COUNT(*) as num_encounters,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY DATE(e.admission_date)) as pct_of_daily_total
FROM fact_encounters e
JOIN dim_departments d ON e.department_key = d.department_key
GROUP BY DATE(e.admission_date), d.department_name, e.admission_type
ORDER BY admission_date DESC, d.department_name, e.admission_type;
