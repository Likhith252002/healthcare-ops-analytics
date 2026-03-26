import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import random
from datetime import timedelta
from tqdm import tqdm
import psycopg2

from utils.db_connection import get_connection
from utils.logger import setup_logger

# Initialize
logger = setup_logger(__name__)


def get_encounters_with_details():
    """
    Retrieve all encounters with fields needed for bed event generation.

    Returns:
        list of tuples: (encounter_key, department_key, admission_date, discharge_date)
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT encounter_key, department_key, admission_date, discharge_date
            FROM fact_encounters
            ORDER BY admission_date
            """
        )
        rows = cursor.fetchall()
        logger.info(f"Retrieved {len(rows)} encounters for bed event generation")
        return rows
    finally:
        cursor.close()
        conn.close()


def get_department_bed_capacity():
    """
    Retrieve bed capacity for each department.

    Returns:
        dict: {department_key (int): bed_capacity (int)}
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT department_key, bed_capacity FROM dim_departments")
        rows = cursor.fetchall()
        bed_capacity_map = {dept_key: capacity for dept_key, capacity in rows}
        logger.info(f"Retrieved bed capacity for {len(bed_capacity_map)} departments")
        return bed_capacity_map
    finally:
        cursor.close()
        conn.close()


def generate_bed_events(encounters, bed_capacity_map):
    """
    Generate bed_assigned and bed_discharged events for each encounter.

    Args:
        encounters (list): Tuples of (encounter_key, department_key, admission_date, discharge_date)
        bed_capacity_map (dict): department_key -> bed_capacity

    Returns:
        list of dicts: One bed_assigned and one bed_discharged event per encounter
    """
    bed_events = []

    for encounter in tqdm(encounters, desc="Generating bed events"):
        encounter_key, department_key, admission_date, discharge_date = encounter
        bed_capacity = bed_capacity_map.get(department_key, 1)
        bed_number = random.randint(1, bed_capacity)

        bed_events.append({
            'encounter_key':   encounter_key,
            'department_key':  department_key,
            'bed_number':      bed_number,
            'event_type':      'bed_assigned',
            'event_timestamp': admission_date,
        })

        bed_events.append({
            'encounter_key':   encounter_key,
            'department_key':  department_key,
            'bed_number':      bed_number,
            'event_type':      'bed_discharged',
            'event_timestamp': discharge_date,
        })

    return bed_events


def insert_bed_events(bed_events):
    """
    Insert bed event records into fact_bed_events.

    Args:
        bed_events (list of dicts): Events to insert
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    sql = """
        INSERT INTO fact_bed_events
            (encounter_key, department_key, bed_number, event_type, event_timestamp)
        VALUES (%s, %s, %s, %s, %s)
    """

    try:
        for i, event in enumerate(tqdm(bed_events, desc="Inserting bed events")):
            cursor.execute(sql, (
                event['encounter_key'],
                event['department_key'],
                event['bed_number'],
                event['event_type'],
                event['event_timestamp'],
            ))
            if (i + 1) % 500 == 0:
                conn.commit()

        conn.commit()  # Final commit for remaining records
        logger.info(f"Successfully inserted {len(bed_events)} bed events")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error during bed event insertion: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    logger.info("Starting bed event generation...")

    encounters = get_encounters_with_details()
    if not encounters:
        raise ValueError("No encounters found. Run generate_encounters.py first")

    bed_capacity_map = get_department_bed_capacity()
    if not bed_capacity_map:
        raise ValueError("No departments found. Run generate_reference_data.py first")

    bed_events = generate_bed_events(encounters, bed_capacity_map)
    insert_bed_events(bed_events)

    logger.info("Bed event generation complete")
    print(f"\n--- Summary ---")
    print(f"Total encounters processed : {len(encounters)}")
    print(f"Total bed events created   : {len(bed_events)}")
    print(f"Events per encounter       : 2 (assigned + discharged)")


if __name__ == "__main__":
    main()
