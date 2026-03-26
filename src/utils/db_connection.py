import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Create and return a PostgreSQL connection using DATABASE_URL from .env."""
    try:
        connection = psycopg2.connect(os.getenv('DATABASE_URL'))
        return connection
    except psycopg2.OperationalError:
        print("ERROR: Could not connect to database. Check .env file.")
        return None


def test_connection():
    """Test the database connection and print PostgreSQL version."""
    try:
        conn = get_connection()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"PostgreSQL version: {version[0]}")
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"ERROR: Connection test failed: {e}")
        return False
