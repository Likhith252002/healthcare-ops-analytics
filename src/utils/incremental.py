import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from datetime import datetime
from typing import Optional, Dict, Any
from utils.db_connection import get_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)


def get_last_load_timestamp(
    table_name: str,
    timestamp_column: str = 'created_at'
) -> Optional[datetime]:
    """
    Get the maximum timestamp from a table.
    Used to determine the starting point for incremental loads.

    Returns None if table is empty.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = f"SELECT MAX({timestamp_column}) FROM {table_name}"
        cursor.execute(query)
        result = cursor.fetchone()

        max_timestamp = result[0] if result and result[0] else None

        if max_timestamp:
            logger.info(
                f"Last load timestamp for {table_name}.{timestamp_column}: {max_timestamp}"
            )
        else:
            logger.info(f"No data found in {table_name}, will perform full load")

        return max_timestamp

    except Exception as e:
        logger.error(f"Error getting last load timestamp: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()


def record_load_metadata(
    table_name: str,
    records_loaded: int,
    start_time: datetime,
    end_time: datetime
) -> None:
    """
    Record metadata about an incremental load run.
    Creates load_history table if it doesn't exist.
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Create load_history table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS load_history (
                load_id SERIAL PRIMARY KEY,
                table_name VARCHAR(100) NOT NULL,
                records_loaded INTEGER NOT NULL,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP NOT NULL,
                duration_seconds NUMERIC(10, 2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Calculate duration
        duration = (end_time - start_time).total_seconds()

        # Insert load record
        cursor.execute("""
            INSERT INTO load_history
            (table_name, records_loaded, start_time, end_time, duration_seconds)
            VALUES (%s, %s, %s, %s, %s)
        """, (table_name, records_loaded, start_time, end_time, duration))

        conn.commit()

        logger.info(
            f"Recorded load metadata: {table_name} - "
            f"{records_loaded} records in {duration:.2f}s"
        )

    except Exception as e:
        logger.error(f"Error recording load metadata: {str(e)}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def detect_changes(
    table_name: str,
    source_data: list,
    key_column: str,
    compare_columns: list
) -> Dict[str, list]:
    """
    Compare source data against existing table data.
    Returns categorized records: new, updated, unchanged.

    Example:
        changes = detect_changes(
            'dim_patients',
            new_patient_data,
            key_column='patient_id',
            compare_columns=['address', 'city', 'phone_number']
        )

        print(f"New: {len(changes['new'])}")
        print(f"Updated: {len(changes['updated'])}")
        print(f"Unchanged: {len(changes['unchanged'])}")
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Extract all keys from source data
    source_keys = [record[key_column] for record in source_data]

    if not source_keys:
        return {'new': [], 'updated': [], 'unchanged': []}

    try:
        # Fetch existing records with matching keys
        placeholders = ','.join(['%s'] * len(source_keys))
        columns_str = ', '.join([key_column] + compare_columns)

        query = f"""
            SELECT {columns_str}
            FROM {table_name}
            WHERE {key_column} IN ({placeholders})
        """

        cursor.execute(query, source_keys)
        existing_records = cursor.fetchall()

        # Build lookup dict of existing records
        existing_dict = {}
        for row in existing_records:
            key = row[0]
            values = row[1:]  # All compare columns
            existing_dict[key] = values

        # Categorize records
        new_records = []
        updated_records = []
        unchanged_records = []

        for record in source_data:
            key = record[key_column]

            if key not in existing_dict:
                # New record
                new_records.append(record)
            else:
                # Compare values
                source_values = tuple(record.get(col) for col in compare_columns)
                existing_values = existing_dict[key]

                if source_values != existing_values:
                    # Updated record
                    updated_records.append(record)
                else:
                    # Unchanged
                    unchanged_records.append(record)

        logger.info(
            f"Change detection: {len(new_records)} new, "
            f"{len(updated_records)} updated, "
            f"{len(unchanged_records)} unchanged"
        )

        return {
            'new': new_records,
            'updated': updated_records,
            'unchanged': unchanged_records
        }

    except Exception as e:
        logger.error(f"Error detecting changes: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()
