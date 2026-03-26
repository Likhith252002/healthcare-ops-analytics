import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import List, Dict, Any
from datetime import datetime

from utils.db_connection import get_connection
from utils.logger import setup_logger

logger = setup_logger(__name__)


class DataQualityTest:
    """Represent a single data quality test."""

    def __init__(self, name, query, severity='error', description=''):
        self.name = name
        self.query = query
        self.severity = severity
        self.description = description

    def run(self) -> Dict[str, Any]:
        """Execute test and return results. Query must return 0 rows to pass."""
        conn = get_connection()
        cursor = conn.cursor()

        start_time = datetime.now()
        cursor.execute(self.query)
        result = cursor.fetchall()
        end_time = datetime.now()

        cursor.close()
        conn.close()

        passed = len(result) == 0

        return {
            'test_name':       self.name,
            'passed':          passed,
            'severity':        self.severity,
            'description':     self.description,
            'failure_count':   len(result),
            'execution_time':  (end_time - start_time).total_seconds(),
            'failed_records':  result[:5] if not passed else [],
        }


def define_tests() -> List[DataQualityTest]:
    """Define all data quality tests across all categories."""
    return [
        # ── NULL Checks ───────────────────────────────────────────────────────
        DataQualityTest(
            name="Patients have no NULL names",
            query="""
                SELECT patient_key FROM dim_patients
                WHERE first_name IS NULL OR last_name IS NULL
            """,
            severity='error',
            description="Patient first_name and last_name must never be NULL",
        ),
        DataQualityTest(
            name="Encounters have valid dates",
            query="""
                SELECT encounter_key FROM fact_encounters
                WHERE admission_date IS NULL OR discharge_date IS NULL
            """,
            severity='error',
            description="Every encounter must have both admission and discharge dates",
        ),

        # ── Referential Integrity ─────────────────────────────────────────────
        DataQualityTest(
            name="All encounters reference valid patients",
            query="""
                SELECT e.encounter_key
                FROM fact_encounters e
                LEFT JOIN dim_patients p ON e.patient_key = p.patient_key
                WHERE p.patient_key IS NULL
            """,
            severity='error',
            description="Every encounter must reference an existing patient record",
        ),
        DataQualityTest(
            name="All encounters reference valid departments",
            query="""
                SELECT e.encounter_key
                FROM fact_encounters e
                LEFT JOIN dim_departments d ON e.department_key = d.department_key
                WHERE d.department_key IS NULL
            """,
            severity='error',
            description="Every encounter must reference an existing department",
        ),
        DataQualityTest(
            name="All bed events reference valid encounters",
            query="""
                SELECT b.bed_event_key
                FROM fact_bed_events b
                LEFT JOIN fact_encounters e ON b.encounter_key = e.encounter_key
                WHERE e.encounter_key IS NULL
            """,
            severity='error',
            description="Every bed event must reference an existing encounter",
        ),

        # ── Business Rules ────────────────────────────────────────────────────
        DataQualityTest(
            name="Discharge dates after admission dates",
            query="""
                SELECT encounter_key FROM fact_encounters
                WHERE discharge_date <= admission_date
            """,
            severity='error',
            description="Discharge date must always be after admission date",
        ),
        DataQualityTest(
            name="Bed numbers within capacity",
            query="""
                SELECT b.bed_event_key
                FROM fact_bed_events b
                JOIN dim_departments d ON b.department_key = d.department_key
                WHERE b.bed_number > d.bed_capacity OR b.bed_number < 1
            """,
            severity='error',
            description="Bed numbers must be between 1 and the department's bed_capacity",
        ),
        DataQualityTest(
            name="Patient ages are reasonable",
            query="""
                SELECT patient_key FROM dim_patients
                WHERE date_of_birth > CURRENT_DATE
                   OR date_of_birth < CURRENT_DATE - INTERVAL '120 years'
            """,
            severity='error',
            description="Patient date_of_birth must produce an age between 0 and 120 years",
        ),

        # ── SCD2 Integrity ────────────────────────────────────────────────────
        DataQualityTest(
            name="Only one current record per patient",
            query="""
                SELECT patient_id FROM dim_patients
                WHERE is_current = TRUE
                GROUP BY patient_id
                HAVING COUNT(*) > 1
            """,
            severity='error',
            description="Each patient_id must have exactly one row where is_current = TRUE",
        ),
        DataQualityTest(
            name="No gaps in patient history",
            query="""
                SELECT p1.patient_id
                FROM dim_patients p1
                JOIN dim_patients p2
                    ON p1.patient_id = p2.patient_id
                    AND p2.record_version = p1.record_version + 1
                WHERE p1.valid_to != p2.valid_from
            """,
            severity='error',
            description="valid_to of version N must equal valid_from of version N+1 (no history gaps)",
        ),
        DataQualityTest(
            name="Current records have valid_to in future",
            query="""
                SELECT patient_key FROM dim_patients
                WHERE is_current = TRUE AND valid_to < CURRENT_TIMESTAMP
            """,
            severity='error',
            description="Any record marked is_current = TRUE must have valid_to in the future",
        ),

        # ── Data Completeness ─────────────────────────────────────────────────
        DataQualityTest(
            name="All departments have physicians",
            query="""
                SELECT d.department_key
                FROM dim_departments d
                LEFT JOIN dim_physicians p ON d.department_key = p.department_key
                WHERE p.physician_key IS NULL
            """,
            severity='warning',
            description="Each department should have at least one physician assigned",
        ),
    ]


def run_all_tests() -> Dict[str, Any]:
    """Run all data quality tests and return a summary dict."""
    tests = define_tests()
    results = []

    for test in tests:
        result = test.run()
        results.append(result)
        if result['passed']:
            logger.info(f"✓ PASSED: {test.name}")
        else:
            logger.error(
                f"✗ FAILED: {test.name} ({result['failure_count']} violations)"
            )

    total_tests = len(results)
    passed      = sum(1 for r in results if r['passed'])
    failed      = total_tests - passed
    errors      = sum(1 for r in results if not r['passed'] and r['severity'] == 'error')
    warnings    = sum(1 for r in results if not r['passed'] and r['severity'] == 'warning')

    return {
        'timestamp':   datetime.now().isoformat(),
        'total_tests': total_tests,
        'passed':      passed,
        'failed':      failed,
        'errors':      errors,
        'warnings':    warnings,
        'tests':       results,
    }
