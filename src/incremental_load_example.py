import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
from utils.incremental import (
    get_last_load_timestamp,
    record_load_metadata,
    detect_changes
)
from utils.logger import setup_logger

logger = setup_logger(__name__)


def incremental_load_encounters():
    """
    Example: Incrementally load new encounters since last load.

    In production, this would:
    1. Query source system for records created/updated since last load
    2. Load only those records
    3. Record metadata about the load
    """

    print("=" * 80)
    print("INCREMENTAL LOAD DEMONSTRATION")
    print("=" * 80)
    print()

    # Step 1: Get last load timestamp
    print("Step 1: Checking last load timestamp...")
    last_load = get_last_load_timestamp('fact_encounters', 'created_at')

    if last_load:
        print(f"  Last load: {last_load}")
        print(f"  Will load records created after this time")
    else:
        print("  No previous loads found")
        print("  Will perform full load")

    print()

    # Step 2: Simulate loading new records
    print("Step 2: Loading new records...")
    start_time = datetime.now()

    # In production, query source system:
    # new_records = query_source_system(
    #     "SELECT * FROM encounters WHERE created_at > %s",
    #     last_load
    # )

    # For demo, just count records that would be loaded
    from utils.db_connection import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    if last_load:
        cursor.execute(
            "SELECT COUNT(*) FROM fact_encounters WHERE created_at > %s",
            (last_load,)
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM fact_encounters")

    records_loaded = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    end_time = datetime.now()

    print(f"  Records to load: {records_loaded}")
    print()

    # Step 3: Record load metadata
    print("Step 3: Recording load metadata...")
    record_load_metadata('fact_encounters', records_loaded, start_time, end_time)
    print("  ✓ Metadata recorded in load_history table")
    print()

    print("=" * 80)
    print("INCREMENTAL LOAD COMPLETE")
    print("=" * 80)
    print()
    print("Query load history:")
    print("  SELECT * FROM load_history ORDER BY created_at DESC;")


def change_detection_example():
    """
    Example: Detect which records are new vs updated.
    """

    print("=" * 80)
    print("CHANGE DETECTION DEMONSTRATION")
    print("=" * 80)
    print()

    # Sample data (in production, this comes from source system)
    sample_patients = [
        {
            'patient_id': 'patient-001',
            'first_name': 'John',
            'last_name': 'Smith',
            'address': '123 Main St',
            'city': 'Boston',
            'phone_number': '555-0100'
        },
        {
            'patient_id': 'patient-002',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'address': '456 Oak Ave',  # Changed address
            'city': 'Cambridge',       # Changed city
            'phone_number': '555-0200'
        },
        {
            'patient_id': 'new-patient-003',  # New patient
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'address': '789 Pine Rd',
            'city': 'Somerville',
            'phone_number': '555-0300'
        }
    ]

    # Detect changes
    changes = detect_changes(
        table_name='dim_patients',
        source_data=sample_patients,
        key_column='patient_id',
        compare_columns=['address', 'city', 'phone_number']
    )

    print(f"New records: {len(changes['new'])}")
    for record in changes['new']:
        print(f"  - {record['patient_id']}: {record['first_name']} {record['last_name']}")
    print()

    print(f"Updated records: {len(changes['updated'])}")
    for record in changes['updated']:
        print(f"  - {record['patient_id']}: {record['first_name']} {record['last_name']}")
    print()

    print(f"Unchanged records: {len(changes['unchanged'])}")
    for record in changes['unchanged']:
        print(f"  - {record['patient_id']}: {record['first_name']} {record['last_name']}")
    print()

    print("=" * 80)
    print("In production, you would:")
    print("  1. INSERT new records")
    print("  2. UPDATE changed records (or use SCD2 pattern)")
    print("  3. SKIP unchanged records (no action needed)")
    print("=" * 80)


def main():
    print("\nRunning incremental load example...\n")
    incremental_load_encounters()

    print("\nRunning change detection example...\n")
    change_detection_example()


if __name__ == "__main__":
    main()
