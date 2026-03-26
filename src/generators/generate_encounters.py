import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from faker import Faker
import uuid
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import psycopg2

from utils.db_connection import get_connection
from utils.logger import setup_logger
from config.settings import DATA_GENERATION, ENCOUNTER_PATTERNS, CHIEF_COMPLAINTS

# Initialize
fake = Faker()
logger = setup_logger(__name__)


def get_patient_keys():
    """Retrieve all patient_key values from dim_patients."""
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT patient_key FROM dim_patients")
        rows = cursor.fetchall()
        patient_keys = [row[0] for row in rows]
        logger.info(f"Retrieved {len(patient_keys)} patient keys")
        return patient_keys
    finally:
        cursor.close()
        conn.close()


def get_department_physician_mapping():
    """
    Build a mapping of department_key -> list of physician_keys.

    Returns:
        dict: {department_key (int): [physician_key, ...]}
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT department_key, physician_key FROM dim_physicians")
        rows = cursor.fetchall()

        dept_physician_map = {}
        for dept_key, phys_key in rows:
            dept_physician_map.setdefault(dept_key, []).append(phys_key)

        logger.info(f"Retrieved physicians for {len(dept_physician_map)} departments")
        return dept_physician_map
    finally:
        cursor.close()
        conn.close()


def generate_admission_date(simulation_days):
    """
    Generate a random admission datetime within the simulation window,
    weighted by day-of-week multiplier using rejection sampling.

    Args:
        simulation_days (int): Number of past days to simulate

    Returns:
        datetime: Admission datetime
    """
    start_date = datetime.now() - timedelta(days=simulation_days)
    multipliers = ENCOUNTER_PATTERNS['weekday_multiplier']
    max_multiplier = max(multipliers.values())

    while True:
        random_day = random.randint(0, simulation_days)
        candidate = start_date + timedelta(days=random_day)
        weekday = candidate.weekday()
        multiplier = multipliers[weekday]

        if random.random() < (multiplier / max_multiplier):
            hour = random.randint(0, 23)
            minute = random.randint(0, 59)
            return candidate.replace(hour=hour, minute=minute, second=0, microsecond=0)


def generate_encounter_record(patient_keys, dept_physician_map, simulation_days):
    """
    Generate a single encounter record.

    Args:
        patient_keys (list): List of valid patient_key integers
        dept_physician_map (dict): department_key -> [physician_key, ...]
        simulation_days (int): Simulation window length

    Returns:
        dict: Encounter fields ready for DB insertion
    """
    admission_type_dist = ENCOUNTER_PATTERNS['admission_type_distribution']
    los_range = ENCOUNTER_PATTERNS['length_of_stay_range']

    encounter_id = str(uuid.uuid4())
    patient_key = random.choice(patient_keys)
    department_key = random.choice(list(dept_physician_map.keys()))
    physician_key = random.choice(dept_physician_map[department_key])
    admission_date = generate_admission_date(simulation_days)
    admission_type = random.choices(
        list(admission_type_dist.keys()),
        weights=list(admission_type_dist.values())
    )[0]
    length_of_stay = random.randint(los_range[0], los_range[1])
    discharge_date = admission_date + timedelta(days=length_of_stay)
    chief_complaint = random.choice(CHIEF_COMPLAINTS)

    return {
        'encounter_id':    encounter_id,
        'patient_key':     patient_key,
        'department_key':  department_key,
        'physician_key':   physician_key,
        'admission_date':  admission_date,
        'discharge_date':  discharge_date,
        'admission_type':  admission_type,
        'chief_complaint': chief_complaint,
    }


def insert_encounters(num_encounters, simulation_days):
    """
    Generate and insert encounter records into fact_encounters.

    Args:
        num_encounters (int): Number of encounters to generate
        simulation_days (int): Simulation window length in days
    """
    patient_keys = get_patient_keys()
    if not patient_keys:
        raise ValueError("No patients found. Run generate_patients.py first")

    dept_physician_map = get_department_physician_mapping()
    if not dept_physician_map:
        raise ValueError("No departments/physicians found. Run generate_reference_data.py first")

    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    sql = """
        INSERT INTO fact_encounters (
            encounter_id, patient_key, department_key, physician_key,
            admission_date, discharge_date, admission_type, chief_complaint
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        for i in tqdm(range(num_encounters), desc="Generating encounters"):
            record = generate_encounter_record(patient_keys, dept_physician_map, simulation_days)
            cursor.execute(sql, (
                record['encounter_id'],
                record['patient_key'],
                record['department_key'],
                record['physician_key'],
                record['admission_date'],
                record['discharge_date'],
                record['admission_type'],
                record['chief_complaint'],
            ))
            if (i + 1) % 100 == 0:
                conn.commit()

        conn.commit()  # Final commit for remaining records
        logger.info(f"Successfully inserted {num_encounters} encounters")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error during encounter insertion: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    logger.info("Starting encounter data generation...")

    num_encounters = DATA_GENERATION['num_encounters']
    simulation_days = DATA_GENERATION['simulation_days']

    insert_encounters(num_encounters, simulation_days)

    start_date = (datetime.now() - timedelta(days=simulation_days)).strftime('%Y-%m-%d')
    end_date = datetime.now().strftime('%Y-%m-%d')

    logger.info("Encounter generation complete")
    print(f"\n--- Summary ---")
    print(f"Total encounters : {num_encounters}")
    print(f"Date range       : {start_date} to {end_date} ({simulation_days} days)")
    print(f"Average per day  : {num_encounters / simulation_days:.1f} encounters")


if __name__ == "__main__":
    main()
