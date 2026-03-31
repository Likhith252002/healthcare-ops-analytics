from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    'owner': 'data-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email': ['data-team@example.com'],
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'data_quality_monitoring',
    default_args=default_args,
    description='Continuous data quality monitoring',
    schedule_interval='0 * * * *',  # Run hourly
    catchup=False,
    tags=['monitoring', 'data-quality'],
)


def check_data_freshness(**context):
    """Alert if data hasn't been updated recently"""
    hook = PostgresHook(postgres_conn_id='healthcare_ops_postgres')

    records = hook.get_records("""
        SELECT
            MAX(created_at) as last_update,
            EXTRACT(EPOCH FROM (NOW() - MAX(created_at))) / 3600 as hours_since_update
        FROM fact_encounters
    """)

    last_update, hours_since = records[0]

    if hours_since > 48:
        raise Exception(
            f"Data is stale! Last update: {last_update} ({hours_since:.1f} hours ago)"
        )

    print(f"✅ Data is fresh. Last update: {last_update}")
    return "success"


def check_anomalies(**context):
    """Check for data anomalies"""
    hook = PostgresHook(postgres_conn_id='healthcare_ops_postgres')

    # Check for unusual admission patterns
    records = hook.get_records("""
        SELECT
            DATE(admission_date) as date,
            COUNT(*) as admissions
        FROM fact_encounters
        WHERE admission_date > CURRENT_DATE - INTERVAL '7 days'
        GROUP BY DATE(admission_date)
        ORDER BY date DESC
        LIMIT 7
    """)

    admission_counts = [r[1] for r in records]
    avg_admissions = sum(admission_counts) / len(admission_counts)

    for date, count in records:
        if count < avg_admissions * 0.3 or count > avg_admissions * 2.0:
            print(
                f"⚠️  Unusual admission volume on {date}: {count} (avg: {avg_admissions:.0f})"
            )

    print("✅ Anomaly check complete")
    return "success"


freshness_task = PythonOperator(
    task_id='check_data_freshness',
    python_callable=check_data_freshness,
    dag=dag,
)

anomaly_task = PythonOperator(
    task_id='check_anomalies',
    python_callable=check_anomalies,
    dag=dag,
)

freshness_task >> anomaly_task
