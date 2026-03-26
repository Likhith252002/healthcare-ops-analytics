import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.db_connection import get_connection
from utils.logger import setup_logger
from utils.performance import time_operation

logger = setup_logger(__name__)


def refresh_materialized_view(view_name, conn):
    """Refresh a single materialized view."""
    logger.info(f"Refreshing materialized view: {view_name}")
    cursor = conn.cursor()
    try:
        with time_operation(f"Refresh {view_name}"):
            cursor.execute(f"REFRESH MATERIALIZED VIEW {view_name}")
            conn.commit()
        logger.info(f"✓ Successfully refreshed: {view_name}")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to refresh {view_name}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def get_view_stats(conn):
    """Get size statistics for all materialized views."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            matviewname,
            pg_size_pretty(pg_total_relation_size('public.' || matviewname)) AS size
        FROM pg_matviews
        WHERE schemaname = 'public'
        ORDER BY matviewname
        """
    )
    results = cursor.fetchall()
    cursor.close()
    return results


def main():
    print("=" * 80)
    print("REFRESHING VISUALIZATION METRICS")
    print("=" * 80)
    print()

    conn = get_connection()
    if conn is None:
        print("ERROR: Could not connect to database.")
        return 1

    views = [
        'mv_daily_hospital_snapshot',
        'mv_department_performance',
        'mv_patient_demographics',
        'mv_weekly_trends',
        'mv_top_complaints',
    ]

    success_count = 0
    for view in views:
        if refresh_materialized_view(view, conn):
            success_count += 1

    print()
    print("=" * 80)
    print("MATERIALIZED VIEW STATISTICS")
    print("=" * 80)

    stats = get_view_stats(conn)
    for view_name, size in stats:
        print(f"{view_name:40} {size:>15}")

    conn.close()

    print()
    print("=" * 80)
    print(f"Refresh complete: {success_count}/{len(views)} views refreshed")
    print("=" * 80)

    if success_count == len(views):
        print("\n✅ All metrics refreshed successfully!")
        return 0
    else:
        print(f"\n⚠️  {len(views) - success_count} view(s) failed to refresh")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
