-- Refresh all materialized views for dashboard metrics
-- Run this after data updates to refresh aggregated metrics

BEGIN;

REFRESH MATERIALIZED VIEW mv_daily_hospital_snapshot;
REFRESH MATERIALIZED VIEW mv_department_performance;
REFRESH MATERIALIZED VIEW mv_patient_demographics;
REFRESH MATERIALIZED VIEW mv_weekly_trends;
REFRESH MATERIALIZED VIEW mv_top_complaints;

COMMIT;

-- Verify refresh
SELECT
    schemaname,
    matviewname,
    pg_size_pretty(pg_total_relation_size(schemaname || '.' || matviewname)) AS size
FROM pg_matviews
WHERE schemaname = 'public'
ORDER BY matviewname;
