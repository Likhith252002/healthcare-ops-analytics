import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

import subprocess
import time
from datetime import datetime

from utils.db_connection import test_connection, get_connection
from utils.logger import setup_logger
from config.settings import DATA_GENERATION

logger = setup_logger(__name__)


def run_script(script_path, description):
    """
    Execute a Python script and track its execution time.

    Args:
        script_path (str): Path to the script (e.g. "src/setup_database.py")
        description (str): Human-readable step label

    Returns:
        bool: True if successful, False on error
    """
    print("=" * 80)
    print(f"STEP: {description}")
    print("=" * 80)
    start_time = time.time()
    try:
        subprocess.run([sys.executable, script_path], check=True)
        elapsed = time.time() - start_time
        print(f"✓ Completed in {elapsed:.2f} seconds\n")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Script failed: {script_path} — {e}")
        print(f"✗ Failed: {description}")
        return False


def validate_data():
    """
    Count rows in all tables to verify data generation.

    Returns:
        dict: {'table_name': row_count}
    """
    conn = get_connection()
    cursor = conn.cursor()
    tables = [
        'dim_patients',
        'dim_departments',
        'dim_physicians',
        'fact_encounters',
        'fact_bed_events',
    ]
    counts = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        counts[table] = count
    cursor.close()
    conn.close()
    return counts


def print_summary(counts, total_time):
    """
    Display the final pipeline summary with row counts and timing.

    Args:
        counts (dict): Table row counts from validate_data()
        total_time (float): Total elapsed seconds for the pipeline
    """
    print("\n" + "=" * 80)
    print("DATA GENERATION SUMMARY")
    print("=" * 80)
    for table, count in counts.items():
        print(f"{table}: {count:,} records")
    print("=" * 80)
    print(f"Total records: {sum(counts.values()):,}")
    print(f"Total time: {total_time:.2f} seconds")
    print("=" * 80)
    encounters = DATA_GENERATION['num_encounters']
    days = DATA_GENERATION['simulation_days']
    avg_per_day = encounters / days
    print("Encounter metrics:")
    print(f"  Simulation period: {days} days")
    print(f"  Total encounters: {encounters:,}")
    print(f"  Average per day: {avg_per_day:.1f}")
    print("=" * 80 + "\n")


def main(reset=False):
    """
    Execute the complete data generation pipeline.

    Args:
        reset (bool): Reserved for future use — drop and recreate schema when True
    """
    print("\n" + "=" * 80)
    print("HEALTHCARE OPERATIONS ANALYTICS PLATFORM")
    print("Data Generation Pipeline")
    print("=" * 80)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    print("Checking database connection...")
    if not test_connection():
        print("✗ Database connection failed. Check your .env file.")
        sys.exit(1)
    print("✓ Database connected\n")

    pipeline_start = time.time()

    steps = [
        ("src/setup_database.py",                     "Setting up database schema"),
        ("src/generators/generate_reference_data.py", "Generating departments and physicians"),
        ("src/generators/generate_patients.py",       "Generating patient demographics"),
        ("src/generators/generate_encounters.py",     "Generating patient encounters"),
        ("src/generators/generate_bed_events.py",     "Generating bed occupancy events"),
    ]

    for script_path, description in steps:
        success = run_script(script_path, description)
        if not success:
            logger.error(f"Pipeline failed at step: {description}")
            print(f"\n✗ Pipeline failed. Check logs for details.")
            sys.exit(1)

    total_time = time.time() - pipeline_start

    print("Validating data...")
    counts = validate_data()
    print_summary(counts, total_time)
    print("✓ Pipeline completed successfully!\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Healthcare Operations Analytics - Data Generation Pipeline"
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and recreate all tables (WARNING: deletes all data)"
    )

    args = parser.parse_args()

    if args.reset:
        confirm = input("WARNING: This will delete all data. Type 'yes' to confirm: ")
        if confirm.lower() != 'yes':
            print("Aborted.")
            sys.exit(0)
        print("Reset flag noted (feature not yet implemented)\n")

    try:
        main(reset=args.reset)
    except KeyboardInterrupt:
        print("\n\n✗ Pipeline interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n✗ Pipeline failed: {e}")
        sys.exit(1)
