import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from faker import Faker
import uuid
from datetime import datetime, timedelta
import random
from tqdm import tqdm
import psycopg2

from utils.db_connection import get_connection
from utils.logger import setup_logger
from utils.retry import retry_with_backoff
from config.settings import DATA_GENERATION, DEMOGRAPHICS

# Initialize
fake = Faker()
logger = setup_logger(__name__)


def generate_patient_record():
    """Generate a single realistic patient record."""
    age_range = DEMOGRAPHICS['age_range']
    gender_dist = DEMOGRAPHICS['gender_distribution']
    insurance_dist = DEMOGRAPHICS['insurance_distribution']

    date_of_birth = datetime.now() - timedelta(
        days=random.randint(age_range[0] * 365, age_range[1] * 365)
    )

    gender = random.choices(
        list(gender_dist.keys()),
        weights=list(gender_dist.values())
    )[0]

    insurance_type = random.choices(
        list(insurance_dist.keys()),
        weights=list(insurance_dist.values())
    )[0]

    return {
        'patient_id':     str(uuid.uuid4()),
        'first_name':     fake.first_name(),
        'last_name':      fake.last_name(),
        'date_of_birth':  date_of_birth.date(),
        'gender':         gender,
        'address':        fake.street_address(),
        'city':           fake.city(),
        'state':          fake.state_abbr(),
        'zip_code':       fake.zipcode(),
        'phone_number':   fake.phone_number(),
        'insurance_type': insurance_type,
    }


def insert_patients(num_patients):
    """Insert num_patients synthetic patient records into dim_patients."""
    conn = get_connection()
    if conn is None:
        raise RuntimeError("Failed to obtain database connection.")

    cursor = conn.cursor()
    sql = """
        INSERT INTO dim_patients (
            patient_id, first_name, last_name, date_of_birth,
            gender, address, city, state, zip_code,
            phone_number, insurance_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    try:
        for i in tqdm(range(num_patients), desc="Generating patients"):
            record = generate_patient_record()
            cursor.execute(sql, (
                record['patient_id'],
                record['first_name'],
                record['last_name'],
                record['date_of_birth'],
                record['gender'],
                record['address'],
                record['city'],
                record['state'],
                record['zip_code'],
                record['phone_number'],
                record['insurance_type'],
            ))
            if (i + 1) % 100 == 0:
                batch_size = min(100, i + 1)

                @retry_with_backoff(
                    max_attempts=3,
                    base_delay=1.0,
                    exceptions=(psycopg2.OperationalError, psycopg2.InterfaceError)
                )
                def commit_batch():
                    conn.commit()

                try:
                    commit_batch()
                    logger.info(f"Committed batch of {batch_size} patients")
                except Exception as e:
                    logger.error(f"Failed to commit batch after retries: {str(e)}")
                    conn.rollback()
                    raise

        conn.commit()  # Final commit for remaining records
        logger.info(f"Successfully inserted {num_patients} patients")

    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"Database error during patient insertion: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def main():
    num_patients = DATA_GENERATION['num_patients']
    logger.info("Starting patient data generation...")
    insert_patients(num_patients)
    logger.info("Patient generation complete")


if __name__ == "__main__":
    main()
