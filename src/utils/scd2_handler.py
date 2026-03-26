import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
import psycopg2
from utils.db_connection import get_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Column names matching dim_patients SELECT order
_PATIENT_COLUMNS = [
    'patient_key', 'patient_id', 'first_name', 'last_name', 'date_of_birth',
    'gender', 'address', 'city', 'state', 'zip_code', 'phone_number',
    'insurance_type', 'valid_from', 'valid_to', 'is_current', 'record_version',
]


def get_current_patient_record(patient_id):
    """
    Retrieve the current active SCD2 record for a patient.

    Args:
        patient_id (str): Business key (UUID)

    Returns:
        dict: Patient data with column names as keys, or None if not found
    """
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT patient_key, patient_id, first_name, last_name, date_of_birth,
                   gender, address, city, state, zip_code, phone_number, insurance_type,
                   valid_from, valid_to, is_current, record_version
            FROM dim_patients
            WHERE patient_id = %s AND is_current = TRUE
            """,
            (patient_id,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return dict(zip(_PATIENT_COLUMNS, row))
    finally:
        cursor.close()
        conn.close()


def expire_current_record(patient_key, effective_date):
    """
    Close out the current SCD2 record by setting valid_to and is_current = FALSE.

    Args:
        patient_key (int): Surrogate key of the record to expire
        effective_date (datetime): When the change takes effect

    Returns:
        bool: True on success, False on exception
    """
    conn = get_connection()
    if conn is None:
        return False

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE dim_patients
            SET valid_to = %s, is_current = FALSE, updated_at = CURRENT_TIMESTAMP
            WHERE patient_key = %s
            """,
            (effective_date, patient_key)
        )
        conn.commit()
        logger.info(f"Expired patient record {patient_key} as of {effective_date}")
        return True
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Failed to expire patient record {patient_key}: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def insert_new_version(patient_data, effective_date):
    """
    Insert a new SCD2 version of a patient record.

    Args:
        patient_data (dict): All patient fields (from the previous current record,
                             already updated with the changed values)
        effective_date (datetime): When this version becomes active

    Returns:
        int: New patient_key, or None on failure
    """
    conn = get_connection()
    if conn is None:
        return None

    cursor = conn.cursor()
    new_version = patient_data.get('record_version', 0) + 1

    try:
        cursor.execute(
            """
            INSERT INTO dim_patients (
                patient_id, first_name, last_name, date_of_birth, gender,
                address, city, state, zip_code, phone_number, insurance_type,
                valid_from, valid_to, is_current, record_version
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING patient_key
            """,
            (
                patient_data['patient_id'],
                patient_data['first_name'],
                patient_data['last_name'],
                patient_data['date_of_birth'],
                patient_data['gender'],
                patient_data['address'],
                patient_data['city'],
                patient_data['state'],
                patient_data['zip_code'],
                patient_data['phone_number'],
                patient_data['insurance_type'],
                effective_date,
                '9999-12-31 23:59:59',
                True,
                new_version,
            )
        )
        new_patient_key = cursor.fetchone()[0]
        conn.commit()
        logger.info(f"Inserted new patient version {new_version} with key {new_patient_key}")
        return new_patient_key
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Failed to insert new patient version: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def update_patient_scd2(patient_id, changes, effective_date=None):
    """
    Main SCD2 update function — expire the current record and insert a new version.

    Args:
        patient_id (str): Business key (UUID)
        changes (dict): Fields that changed, e.g. {'address': '123 New St', 'city': 'Boston'}
        effective_date (datetime, optional): When the change takes effect (defaults to now)

    Returns:
        dict: {'success': bool, 'message': str, 'new_patient_key': int or None}
    """
    if effective_date is None:
        effective_date = datetime.now()

    current_record = get_current_patient_record(patient_id)
    if current_record is None:
        logger.error(f"No current record found for patient {patient_id}")
        return {'success': False, 'message': 'Patient not found'}

    # Check whether any values actually differ
    has_changes = any(
        changes[key] != current_record.get(key)
        for key in changes
    )
    if not has_changes:
        logger.info(f"No actual changes detected for patient {patient_id}")
        return {'success': True, 'message': 'No changes needed'}

    # Expire the current row
    expire_current_record(current_record['patient_key'], effective_date)

    # Build updated record and insert as new version
    updated_record = {**current_record, **changes}
    updated_record['valid_from'] = effective_date

    new_key = insert_new_version(updated_record, effective_date)
    new_version = current_record['record_version'] + 1

    return {
        'success': True,
        'message': f'Created version {new_version}',
        'new_patient_key': new_key,
    }
