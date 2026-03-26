import psycopg2
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).parent))
from utils.db_connection import get_connection


def setup_database():
    print("Starting database setup...")

    conn = get_connection()
    if conn is None:
        sys.exit(1)

    schema_path = Path(__file__).parent.parent / 'sql' / 'schema.sql'
    sql_content = schema_path.read_text()

    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    cursor = conn.cursor()
    try:
        for statement in statements:
            cursor.execute(statement)
            conn.commit()
            print(f"✓ Executed: {statement[:50]}...")
    except Exception as e:
        conn.rollback()
        print(f"ERROR: Failed to execute statement: {e}")
        print(f"Statement: {statement}")
        cursor.close()
        conn.close()
        sys.exit(1)

    cursor.close()
    conn.close()

    print("✓ Database setup complete!")
    print("Tables created: dim_patients, dim_departments, dim_physicians, fact_encounters, fact_bed_events")


if __name__ == "__main__":
    setup_database()
