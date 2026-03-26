import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from utils.performance import benchmark_query, explain_analyze, get_table_sizes, get_index_usage
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    print("=" * 80)
    print("QUERY PERFORMANCE BENCHMARK")
    print("=" * 80)
    print()

    queries = {
        "Current patients (indexed)": (
            "SELECT * FROM dim_patients WHERE is_current = TRUE LIMIT 100"
        ),
        "ER encounters count": (
            "SELECT COUNT(*) FROM fact_encounters e "
            "JOIN dim_departments d ON e.department_key = d.department_key "
            "WHERE d.department_name = 'Emergency Department'"
        ),
        "Bed utilization (last 7 days)": (
            "SELECT department_key, COUNT(*) FROM fact_bed_events "
            "WHERE event_timestamp > CURRENT_DATE - INTERVAL '7 days' "
            "GROUP BY department_key"
        ),
        "Patient by business key": (
            "SELECT * FROM dim_patients "
            "WHERE patient_id = (SELECT patient_id FROM dim_patients LIMIT 1) "
            "AND is_current = TRUE"
        ),
    }

    print("QUERY BENCHMARKS (3 iterations each):")
    print("-" * 80)

    for query_name, query in queries.items():
        print(f"\n{query_name}:")
        result = benchmark_query(query, iterations=3)
        print(f"  Avg: {result['avg_time'] * 1000:.2f}ms")
        print(f"  Min: {result['min_time'] * 1000:.2f}ms")
        print(f"  Max: {result['max_time'] * 1000:.2f}ms")

    print("\n" + "=" * 80)
    print("TABLE SIZES")
    print("=" * 80)

    sizes = get_table_sizes()
    for table_name, size_pretty, size_bytes in sizes:
        print(f"{table_name:40} {size_pretty:>15}")

    print("\n" + "=" * 80)
    print("INDEX USAGE STATISTICS")
    print("=" * 80)
    print(f"{'Index Name':<40} {'Table':<30} {'Scans':>10}")
    print("-" * 80)

    usage = get_index_usage()
    for index_name, table_name, scans, _, _ in usage[:10]:  # Top 10
        print(f"{index_name:<40} {table_name:<30} {scans:>10}")

    print("\n" + "=" * 80)
    print("Benchmark complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
