"""
ML Model Training Script

Loads encounter data from PostgreSQL, engineers features, trains both ML models,
evaluates performance, and saves artifacts to ml/saved_models/.

Usage:
    python ml/train_models.py
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from src.utils.db_connection import get_connection
from ml.models.readmission_model import ReadmissionRiskModel
from ml.models.los_model import LOSPredictionModel


TRAINING_QUERY = """
SELECT
    fe.encounter_id,
    fe.patient_id,
    fe.admission_date,
    fe.discharge_date,
    fe.length_of_stay,
    fe.diagnosis_category,
    dd.department_name,

    -- Patient demographics
    DATE_PART('year', AGE(dp.date_of_birth)) AS age,
    dp.insurance_type,

    -- Previous visits (lookback)
    COALESCE(prev.num_previous_visits, 0) AS num_previous_visits,

    -- Readmission target: another visit within 30 days of discharge
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM fact_encounters re
            WHERE re.patient_id = fe.patient_id
              AND re.encounter_id != fe.encounter_id
              AND re.admission_date BETWEEN fe.discharge_date
                  AND fe.discharge_date + INTERVAL '30 days'
        ) THEN 1
        ELSE 0
    END AS readmitted_30d

FROM fact_encounters fe
JOIN dim_departments dd ON fe.department_id = dd.department_id
JOIN dim_patients dp
    ON fe.patient_id = dp.patient_id
    AND dp.is_current = TRUE
LEFT JOIN (
    SELECT
        patient_id,
        admission_date,
        COUNT(*) OVER (
            PARTITION BY patient_id
            ORDER BY admission_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
        ) AS num_previous_visits
    FROM fact_encounters
) prev ON fe.patient_id = prev.patient_id
       AND fe.admission_date = prev.admission_date

WHERE fe.discharge_date IS NOT NULL
  AND fe.length_of_stay > 0
ORDER BY fe.admission_date
"""


def load_training_data() -> pd.DataFrame:
    """Load and return the training dataset from PostgreSQL."""
    conn = get_connection()
    try:
        df = pd.read_sql(TRAINING_QUERY, conn)
        print(f"Loaded {len(df):,} encounters for training")
        print(f"Readmission rate: {df['readmitted_30d'].mean():.1%}")
        print(f"Avg LOS: {df['length_of_stay'].mean():.1f} days")
        return df
    finally:
        conn.close()


def train_readmission_model(df: pd.DataFrame) -> dict:
    """Train and save the readmission risk model."""
    print("\n--- Training Readmission Risk Model ---")
    model = ReadmissionRiskModel()
    metrics = model.train(df)
    model.save()
    return metrics


def train_los_model(df: pd.DataFrame) -> dict:
    """Train and save the LOS prediction model."""
    print("\n--- Training Length of Stay Model ---")
    model = LOSPredictionModel()
    metrics = model.train(df)
    model.save()
    return metrics


def main():
    print("=" * 60)
    print("Healthcare ML Model Training")
    print("=" * 60)

    df = load_training_data()

    if len(df) < 500:
        print(
            f"Warning: Only {len(df)} records available. "
            "Generate more data with: python src/main.py"
        )

    readmission_metrics = train_readmission_model(df)
    los_metrics = train_los_model(df)

    print("\n" + "=" * 60)
    print("Training Complete — Summary")
    print("=" * 60)
    print(f"Readmission Model  ROC-AUC : {readmission_metrics['roc_auc']:.4f}")
    print(f"LOS Model          MAE     : {los_metrics['mae']:.2f} days")
    print(f"LOS Model          RMSE    : {los_metrics['rmse']:.2f} days")
    print(f"LOS Model          R²      : {los_metrics['r2']:.4f}")
    print("\nModels saved to: ml/saved_models/")


if __name__ == "__main__":
    main()
