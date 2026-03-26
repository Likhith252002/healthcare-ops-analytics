import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from contextlib import contextmanager
from typing import Dict, List, Tuple
import psycopg2

from utils.db_connection import get_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)


def benchmark_query(query, params=None, iterations=3):
    """
    Measure query execution time over multiple runs.

    Args:
        query (str): SQL query to benchmark
        params (tuple): Query parameters (optional)
        iterations (int): Number of times to run (default 3)

    Returns:
        dict: {'avg_time', 'min_time', 'max_time', 'iterations', 'all_times'}
    """
    execution_times = []

    for i in range(iterations):
        conn = get_connection()
        cursor = conn.cursor()
        start_time = time.time()
        cursor.execute(query, params if params else ())
        cursor.fetchall()  # Ensure full execution including data transfer
        end_time = time.time()
        elapsed = end_time - start_time
        execution_times.append(elapsed)
        cursor.close()
        conn.close()
        logger.info(f"Iteration {i + 1}: {elapsed:.4f}s")

    avg_time = sum(execution_times) / len(execution_times)
    min_time = min(execution_times)
    max_time = max(execution_times)

    return {
        'avg_time':   avg_time,
        'min_time':   min_time,
        'max_time':   max_time,
        'iterations': iterations,
        'all_times':  execution_times,
    }


def explain_analyze(query, params=None):
    """
    Get PostgreSQL EXPLAIN ANALYZE execution plan for a query.

    Args:
        query (str): SQL query to analyze
        params (tuple): Query parameters (optional)

    Returns:
        str: Formatted execution plan
    """
    conn = get_connection()
    cursor = conn.cursor()
    explain_query = f"EXPLAIN ANALYZE {query}"
    cursor.execute(explain_query, params if params else ())
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return "\n".join(row[0] for row in rows)


@contextmanager
def time_operation(operation_name: str):
    """
    Context manager to measure and log execution time of a code block.

    Usage:
        with time_operation("Data generation"):
            # code here
    """
    start_time = time.time()
    logger.info(f"Starting: {operation_name}")
    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Completed: {operation_name} in {elapsed:.2f}s")


def get_table_sizes():
    """
    Get size of all tables in the public schema.

    Returns:
        list of tuples: (table_name, size_pretty, size_bytes)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            schemaname || '.' || tablename as table_name,
            pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size_pretty,
            pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
        """
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results


def get_index_usage():
    """
    Show index usage statistics ordered by most-used first.

    Returns:
        list of tuples: (index_name, table_name, scans, tuples_read, tuples_fetched)
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            indexrelname as index_name,
            relname as table_name,
            idx_scan as scans,
            idx_tup_read as tuples_read,
            idx_tup_fetch as tuples_fetched
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC
        """
    )
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results
