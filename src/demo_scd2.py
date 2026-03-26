import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from datetime import datetime, timedelta
from utils.scd2_handler import update_patient_scd2, get_current_patient_record
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    print("=" * 80)
    print("TYPE 2 SLOWLY CHANGING DIMENSION (SCD2) DEMONSTRATION")
    print("=" * 80)
    print()

    # Fetch a real patient_id from the database to use as the demo subject
    from utils.db_connection import get_connection
    conn = get_connection()
    if conn is None:
        print("ERROR: Could not connect to database. Run src/main.py first.")
        sys.exit(1)

    cursor = conn.cursor()
    cursor.execute("SELECT patient_id FROM dim_patients WHERE is_current = TRUE LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()

    if row is None:
        print("ERROR: No patients found. Run src/main.py to generate data first.")
        sys.exit(1)

    patient_id = row[0]
    print(f"Scenario: Patient {patient_id} moved to a new address")
    print()

    # ── BEFORE ────────────────────────────────────────────────────────────────
    print("BEFORE UPDATE:")
    current = get_current_patient_record(patient_id)
    if current:
        print(f"  Address  : {current['address']}, {current['city']}, {current['state']}")
        print(f"  Valid From: {current['valid_from']}")
        print(f"  Version  : {current['record_version']}")
    print()

    # ── APPLY SCD2 UPDATE ─────────────────────────────────────────────────────
    changes = {
        'address':  '456 New Street',
        'city':     'Boston',
        'state':    'MA',
        'zip_code': '02101',
    }

    effective_date = datetime.now()
    result = update_patient_scd2(patient_id, changes, effective_date)

    print("UPDATE APPLIED:")
    print(f"  Status: {result['message']}")
    print()

    # ── AFTER ─────────────────────────────────────────────────────────────────
    print("AFTER UPDATE:")
    current = get_current_patient_record(patient_id)
    if current:
        print(f"  Address  : {current['address']}, {current['city']}, {current['state']}")
        print(f"  Valid From: {current['valid_from']}")
        print(f"  Version  : {current['record_version']}")
    print()

    print("=" * 80)
    print("SCD2 demonstration complete!")
    print("Historical records are preserved - old address is still queryable")
    print("=" * 80)


if __name__ == "__main__":
    main()
