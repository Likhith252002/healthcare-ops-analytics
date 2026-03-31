"""Prometheus metrics for the Healthcare Operations platform."""
import sys
from pathlib import Path

# Ensure src/utils is importable when this module is loaded standalone
_project_root = Path(__file__).parent.parent
sys.path.insert(0, str(_project_root / "src"))

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# ─────────────────────────────────────────────────────────────────────────────
# HTTP metrics
# ─────────────────────────────────────────────────────────────────────────────

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Database metrics
# ─────────────────────────────────────────────────────────────────────────────

database_queries_total = Counter(
    "database_queries_total",
    "Total database queries",
    ["table", "operation"],
)

database_query_duration_seconds = Histogram(
    "database_query_duration_seconds",
    "Database query duration",
    ["table", "operation"],
)

# ─────────────────────────────────────────────────────────────────────────────
# ML metrics
# ─────────────────────────────────────────────────────────────────────────────

ml_predictions_total = Counter(
    "ml_predictions_total",
    "Total ML predictions",
    ["model", "status"],
)

ml_prediction_duration_seconds = Histogram(
    "ml_prediction_duration_seconds",
    "ML prediction duration",
    ["model"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Data quality / ETL metrics
# ─────────────────────────────────────────────────────────────────────────────

data_quality_checks_total = Counter(
    "data_quality_checks_total",
    "Total data quality checks",
    ["check_name", "status"],
)

etl_runs_total = Counter(
    "etl_runs_total",
    "Total ETL pipeline runs",
    ["status"],
)

etl_duration_seconds = Histogram(
    "etl_duration_seconds",
    "ETL pipeline duration in seconds",
)

# ─────────────────────────────────────────────────────────────────────────────
# Current-state gauges
# ─────────────────────────────────────────────────────────────────────────────

active_patients = Gauge("active_patients", "Number of active patients")
total_encounters = Gauge("total_encounters", "Total encounters")
avg_length_of_stay = Gauge("avg_length_of_stay", "Average length of stay in days")


def update_gauges() -> None:
    """Refresh gauge metrics from the live database."""
    from utils.db_connection import get_connection

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM dim_patients WHERE is_current = TRUE")
        active_patients.set(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM fact_encounters")
        total_encounters.set(cursor.fetchone()[0])

        cursor.execute(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400.0)
            FROM fact_encounters
            WHERE discharge_date IS NOT NULL
            """
        )
        result = cursor.fetchone()[0]
        if result is not None:
            avg_length_of_stay.set(float(result))
    finally:
        cursor.close()
        conn.close()
