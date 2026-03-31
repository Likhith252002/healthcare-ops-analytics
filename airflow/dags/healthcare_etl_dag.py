from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import sys
from pathlib import Path

# Add project to path
sys.path.append(str(Path(__file__).parent.parent.parent))

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'healthcare_etl_pipeline',
    default_args=default_args,
    description='Daily ETL pipeline for healthcare operations data',
    schedule_interval='0 2 * * *',  # Run daily at 2 AM
    catchup=False,
    tags=['healthcare', 'etl', 'production'],
)


# Task 1: Data Quality Checks
def run_data_quality_checks(**context):
    """Run data quality checks before ETL"""
    import subprocess
    result = subprocess.run(
        ['python', 'src/run_data_quality.py'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Data quality checks failed: {result.stderr}")

    print("✅ Data quality checks passed")
    return "success"


data_quality_task = PythonOperator(
    task_id='data_quality_checks',
    python_callable=run_data_quality_checks,
    dag=dag,
)


# Task 2: Generate Incremental Data
def generate_incremental_data(**context):
    """Generate new data incrementally"""
    from src.generators.generate_patients import insert_patients
    from src.generators.generate_encounters import insert_encounters
    from src.utils.db_connection import get_connection
    from src.utils.incremental import get_last_load_timestamp

    conn = get_connection()

    # Check last load time
    last_load = get_last_load_timestamp('fact_encounters', 'created_at')

    if last_load:
        print(f"Last load: {last_load}. Running incremental load.")
        num_new_patients = 50
        num_new_encounters = 150
    else:
        print("No previous load found. Running full load.")
        num_new_patients = 5000
        num_new_encounters = 15000

    conn.close()

    # Generate data using existing generators
    insert_patients(num_new_patients)
    insert_encounters(num_new_encounters)

    return f"Generated {num_new_patients} patients, {num_new_encounters} encounters"


generate_data_task = PythonOperator(
    task_id='generate_incremental_data',
    python_callable=generate_incremental_data,
    dag=dag,
)


# Task 3: Run dbt Models
dbt_run_task = BashOperator(
    task_id='run_dbt_models',
    bash_command='cd dbt && dbt run --profiles-dir .',
    dag=dag,
)


# Task 4: Run dbt Tests
dbt_test_task = BashOperator(
    task_id='run_dbt_tests',
    bash_command='cd dbt && dbt test --profiles-dir .',
    dag=dag,
)


# Task 5: Refresh Materialized Views
def refresh_materialized_views(**context):
    """Refresh all materialized views"""
    import subprocess
    result = subprocess.run(
        ['python', 'src/refresh_viz_metrics.py'],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise Exception(f"Materialized view refresh failed: {result.stderr}")

    print("✅ Materialized views refreshed")
    return "success"


refresh_views_task = PythonOperator(
    task_id='refresh_materialized_views',
    python_callable=refresh_materialized_views,
    dag=dag,
)


# Task 6: Update Statistics
update_stats_task = PostgresOperator(
    task_id='update_table_statistics',
    postgres_conn_id='healthcare_ops_postgres',
    sql="""
        ANALYZE dim_patients;
        ANALYZE dim_departments;
        ANALYZE dim_physicians;
        ANALYZE fact_encounters;
        ANALYZE fact_bed_events;
    """,
    dag=dag,
)


# Task 7: Validation
def validate_pipeline_results(**context):
    """Validate pipeline ran successfully"""
    hook = PostgresHook(postgres_conn_id='healthcare_ops_postgres')

    # Check record counts
    records = hook.get_records("""
        SELECT
            (SELECT COUNT(*) FROM dim_patients WHERE is_current = TRUE) as patients,
            (SELECT COUNT(*) FROM fact_encounters) as encounters,
            (SELECT MAX(created_at) FROM fact_encounters) as last_encounter
    """)

    patients, encounters, last_encounter = records[0]

    print(f"✅ Pipeline validation:")
    print(f"  - Patients: {patients}")
    print(f"  - Encounters: {encounters}")
    print(f"  - Last encounter: {last_encounter}")

    # Basic sanity checks
    if patients < 1000:
        raise Exception(f"Too few patients: {patients}")
    if encounters < 5000:
        raise Exception(f"Too few encounters: {encounters}")

    return "success"


validation_task = PythonOperator(
    task_id='validate_pipeline_results',
    python_callable=validate_pipeline_results,
    dag=dag,
)


# Define task dependencies
(
    data_quality_task
    >> generate_data_task
    >> dbt_run_task
    >> dbt_test_task
    >> refresh_views_task
    >> update_stats_task
    >> validation_task
)
