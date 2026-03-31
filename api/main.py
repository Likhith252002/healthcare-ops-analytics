"""
Healthcare Operations REST API

FastAPI application providing programmatic access to healthcare data and ML predictions.

Run: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
Docs: http://localhost:8000/docs
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, date
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from utils.db_connection import get_connection

# Try to load ML models (optional — requires python ml/train_models.py first)
try:
    from ml.models.readmission_model import ReadmissionRiskModel
    from ml.models.los_model import LOSPredictionModel

    READMISSION_MODEL = ReadmissionRiskModel.load()
    LOS_MODEL = LOSPredictionModel.load()
    ML_AVAILABLE = True
except Exception:
    ML_AVAILABLE = False
    READMISSION_MODEL = None
    LOS_MODEL = None
    print("⚠️  ML models not available. Train models first: python ml/train_models.py")

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Healthcare Operations API",
    description="REST API for healthcare analytics data and ML predictions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────


class Patient(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    insurance_type: str
    city: Optional[str]
    state: Optional[str]


class Encounter(BaseModel):
    encounter_key: int
    patient_id: str
    admission_date: datetime
    discharge_date: Optional[datetime]
    admission_type: str
    department_name: str
    chief_complaint: Optional[str]


class Department(BaseModel):
    department_key: int
    department_name: str
    bed_capacity: int


class ReadmissionRiskRequest(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    is_male: int = Field(..., ge=0, le=1, description="1=Male, 0=Female")
    is_emergency: int = Field(..., ge=0, le=1, description="1=Emergency admission")
    is_uninsured: int = Field(..., ge=0, le=1, description="1=Self-pay / uninsured")
    los_days: float = Field(..., ge=0, description="Current/recent length of stay in days")
    prior_visits: int = Field(..., ge=0, description="Number of previous hospital visits")


class LOSPredictionRequest(BaseModel):
    age: int = Field(..., ge=0, le=120, description="Patient age in years")
    is_male: int = Field(..., ge=0, le=1, description="1=Male, 0=Female")
    is_emergency: int = Field(..., ge=0, le=1, description="1=Emergency admission")
    bed_capacity: int = Field(..., ge=1, description="Department bed capacity")
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week (0=Monday)")
    hour_of_day: int = Field(..., ge=0, le=23, description="Hour of admission (0-23)")


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build DataFrames for ML models from request fields
# ─────────────────────────────────────────────────────────────────────────────

_INSURANCE_MAP = {0: "Medicare", 1: "Self-Pay"}
_SEVERITY_BY_EMERGENCY = {0: "General", 1: "Cardiac"}  # emergency → higher severity


def _readmission_df(req: ReadmissionRiskRequest) -> pd.DataFrame:
    """Build a feature DataFrame compatible with ReadmissionRiskModel."""
    return pd.DataFrame(
        [
            {
                "age": req.age,
                "length_of_stay": req.los_days,
                "num_previous_visits": req.prior_visits,
                "department_name": "General",
                "diagnosis_category": _SEVERITY_BY_EMERGENCY[req.is_emergency],
                "insurance_type": _INSURANCE_MAP[req.is_uninsured],
            }
        ]
    )


def _los_df(req: LOSPredictionRequest) -> pd.DataFrame:
    """Build a feature DataFrame compatible with LOSPredictionModel."""
    # Construct a synthetic admission_date that carries the correct hour
    base_date = datetime(2024, 1, 7 + req.day_of_week, req.hour_of_day, 0)
    return pd.DataFrame(
        [
            {
                "age": req.age,
                "num_previous_visits": 0,
                "department_name": "General",
                "diagnosis_category": _SEVERITY_BY_EMERGENCY[req.is_emergency],
                "insurance_type": _INSURANCE_MAP.get(0, "Medicare"),
                "admission_date": base_date,
            }
        ]
    )


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/")
def root():
    """API health check."""
    return {
        "status": "healthy",
        "api": "Healthcare Operations API",
        "version": "1.0.0",
        "ml_models_available": ML_AVAILABLE,
    }


@app.get("/patients", response_model=List[Patient])
def get_patients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    """Get list of patients (paginated)."""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT
                patient_id,
                first_name,
                last_name,
                date_of_birth,
                gender,
                insurance_type,
                city,
                state
            FROM dim_patients
            WHERE is_current = TRUE
            ORDER BY patient_id
            LIMIT %s OFFSET %s
            """,
            conn,
            params=[limit, offset],
        )
    finally:
        conn.close()

    return df.to_dict("records")


@app.get("/patients/{patient_id}", response_model=Patient)
def get_patient(patient_id: str):
    """Get a specific patient by business key (patient_id)."""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT
                patient_id,
                first_name,
                last_name,
                date_of_birth,
                gender,
                insurance_type,
                city,
                state
            FROM dim_patients
            WHERE patient_id = %s AND is_current = TRUE
            """,
            conn,
            params=[patient_id],
        )
    finally:
        conn.close()

    if df.empty:
        raise HTTPException(status_code=404, detail="Patient not found")

    return df.to_dict("records")[0]


@app.get("/encounters", response_model=List[Encounter])
def get_encounters(
    patient_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Get list of encounters, optionally filtered by patient_id."""
    conn = get_connection()
    try:
        if patient_id:
            df = pd.read_sql(
                """
                SELECT
                    e.encounter_key,
                    p.patient_id,
                    e.admission_date,
                    e.discharge_date,
                    e.admission_type,
                    d.department_name,
                    e.chief_complaint
                FROM fact_encounters e
                JOIN dim_departments d ON e.department_key = d.department_key
                JOIN dim_patients    p ON e.patient_key  = p.patient_key
                                      AND p.is_current   = TRUE
                WHERE p.patient_id = %s
                ORDER BY e.admission_date DESC
                LIMIT %s
                """,
                conn,
                params=[patient_id, limit],
            )
        else:
            df = pd.read_sql(
                """
                SELECT
                    e.encounter_key,
                    p.patient_id,
                    e.admission_date,
                    e.discharge_date,
                    e.admission_type,
                    d.department_name,
                    e.chief_complaint
                FROM fact_encounters e
                JOIN dim_departments d ON e.department_key = d.department_key
                JOIN dim_patients    p ON e.patient_key  = p.patient_key
                                      AND p.is_current   = TRUE
                ORDER BY e.admission_date DESC
                LIMIT %s
                """,
                conn,
                params=[limit],
            )
    finally:
        conn.close()

    return df.to_dict("records")


@app.get("/departments", response_model=List[Department])
def get_departments():
    """Get list of all departments."""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT
                department_key,
                department_name,
                bed_capacity
            FROM dim_departments
            ORDER BY department_name
            """,
            conn,
        )
    finally:
        conn.close()

    return df.to_dict("records")


@app.get("/stats/summary")
def get_summary_stats():
    """Get high-level summary statistics."""
    conn = get_connection()
    try:
        df = pd.read_sql(
            """
            SELECT
                (SELECT COUNT(*) FROM dim_patients WHERE is_current = TRUE) AS total_patients,
                (SELECT COUNT(*) FROM fact_encounters)                       AS total_encounters,
                (SELECT COUNT(*) FROM dim_departments)                       AS total_departments,
                (SELECT COUNT(*) FROM dim_physicians)                        AS total_physicians,
                (
                    SELECT AVG(
                        EXTRACT(EPOCH FROM (discharge_date - admission_date)) / 86400.0
                    )
                    FROM fact_encounters
                    WHERE discharge_date IS NOT NULL
                ) AS avg_los_days
            """,
            conn,
        )
    finally:
        conn.close()

    stats = df.to_dict("records")[0]
    if stats["avg_los_days"] is not None:
        stats["avg_los_days"] = round(float(stats["avg_los_days"]), 2)

    return stats


@app.post("/predict/readmission")
def predict_readmission(request: ReadmissionRiskRequest):
    """Predict 30-day readmission risk using the trained RandomForest model."""
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Train models first: python ml/train_models.py",
        )

    df = _readmission_df(request)
    probability = float(READMISSION_MODEL.predict_proba(df)[0])
    risk_score = round(probability * 100, 1)

    if risk_score >= 70:
        prediction = "High Risk"
    elif risk_score >= 40:
        prediction = "Medium Risk"
    else:
        prediction = "Low Risk"

    return {
        "risk_score": risk_score,
        "prediction": prediction,
        "probability": round(probability, 4),
    }


@app.post("/predict/los")
def predict_los(request: LOSPredictionRequest):
    """Predict inpatient length of stay (days) using the trained RandomForest model."""
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Train models first: python ml/train_models.py",
        )

    df = _los_df(request)

    # Collect individual tree predictions for a simple confidence interval
    X = LOS_MODEL.prepare_features(df, fit=False)
    tree_preds = np.array(
        [tree.predict(X)[0] for tree in LOS_MODEL.model.estimators_]
    )
    predicted_los = float(np.clip(tree_preds.mean(), 0, None))
    margin = float(1.96 * tree_preds.std())

    return {
        "predicted_los": round(predicted_los, 1),
        "confidence_interval": [
            round(max(0.0, predicted_los - margin), 1),
            round(predicted_los + margin, 1),
        ],
    }
