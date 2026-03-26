import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from faker import Faker
import uuid
import random
from tqdm import tqdm
import psycopg2

from utils.db_connection import get_connection
from utils.logger import setup_logger
from config.settings import DATA_GENERATION, DEPARTMENTS

# Initialize
fake = Faker()
logger = setup_logger(__name__)


def insert_departments():
    """
    Insert all departments from config into dim_departments.

    Returns:
        dict: mapping department_id (UUID str) -> department_key (surrogate int)
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    department_mapping = {}

    try:
        for name, bed_capacity, specialties in DEPARTMENTS:
            department_id = str(uuid.uuid4())

            cursor.execute(
                """
                INSERT INTO dim_departments (department_id, department_name, bed_capacity)
                VALUES (%s, %s, %s)
                """,
                (department_id, name, bed_capacity)
            )

            cursor.execute(
                "SELECT department_key FROM dim_departments WHERE department_id = %s",
                (department_id,)
            )
            department_key = cursor.fetchone()[0]
            department_mapping[department_id] = department_key

            logger.info(f"Inserted department: {name} ({bed_capacity} beds)")

        conn.commit()

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error during department insertion: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

    return department_mapping


def insert_physicians(department_mapping, num_physicians):
    """
    Insert synthetic physician records linked to departments by specialty.

    Args:
        department_mapping (dict): department_id -> department_key
        num_physicians (int): number of physicians to generate
    """
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()

    # Build specialty -> department_key lookup using DB-backed name resolution
    # Also flatten all specialties into a list for random selection
    specialty_to_dept_key = {}
    all_specialties = []

    try:
        for name, _bed_capacity, specialties in DEPARTMENTS:
            cursor.execute(
                "SELECT department_key FROM dim_departments WHERE department_name = %s",
                (name,)
            )
            row = cursor.fetchone()
            if row:
                dept_key = row[0]
                for specialty in specialties:
                    specialty_to_dept_key[specialty] = dept_key
                    all_specialties.append(specialty)

        try:
            for i in tqdm(range(num_physicians), desc="Generating physicians"):
                physician_id = str(uuid.uuid4())
                first_name = fake.first_name()
                last_name = fake.last_name()
                specialty = random.choice(all_specialties)
                dept_key = specialty_to_dept_key[specialty]

                cursor.execute(
                    """
                    INSERT INTO dim_physicians
                        (physician_id, first_name, last_name, specialty, department_key)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (physician_id, first_name, last_name, specialty, dept_key)
                )

                if (i + 1) % 10 == 0:
                    conn.commit()

            conn.commit()  # Final commit for remaining records
            logger.info(f"Successfully inserted {num_physicians} physicians")

        except psycopg2.Error as e:
            conn.rollback()
            logger.error(f"Database error during physician insertion: {e}")
            raise

    finally:
        cursor.close()
        conn.close()


def main():
    logger.info("Starting reference data generation...")

    logger.info("Inserting departments...")
    dept_mapping = insert_departments()

    logger.info("Inserting physicians...")
    num_physicians = DATA_GENERATION['num_physicians']
    insert_physicians(dept_mapping, num_physicians)

    logger.info("Reference data generation complete")

    print(f"\n--- Summary ---")
    print(f"Total departments : {len(DEPARTMENTS)}")
    print(f"Total physicians  : {num_physicians}")
    print(f"Physicians per department (avg): {num_physicians / len(DEPARTMENTS):.1f}")


if __name__ == "__main__":
    main()
