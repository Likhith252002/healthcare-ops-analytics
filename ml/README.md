# ML Models

scikit-learn models for readmission risk prediction and length-of-stay forecasting.

## Models

### Readmission Risk (`ReadmissionRiskModel`)

Predicts probability of 30-day hospital readmission.

- **Algorithm:** RandomForestClassifier (100 trees, max_depth=8)
- **Features:** age, length_of_stay, num_previous_visits, department, diagnosis_severity, insurance_type
- **Metric:** ROC-AUC
- **Target:** Binary — 1 if readmitted within 30 days

### Length of Stay (`LOSPredictionModel`)

Predicts expected inpatient length of stay in days.

- **Algorithm:** RandomForestRegressor (100 trees, max_depth=10)
- **Features:** age, num_previous_visits, department, diagnosis_severity, insurance_type, admission_hour
- **Metrics:** MAE, RMSE, R²
- **Target:** Continuous — days (clipped 0–60)

## Training

```bash
# Prerequisites: database populated with encounter data
python ml/train_models.py
```

Saved artifacts: `ml/saved_models/`

## Usage

```python
from ml.models import ReadmissionRiskModel, LOSPredictionModel
import pandas as pd

# Load a trained model
readmission_model = ReadmissionRiskModel.load()
los_model = LOSPredictionModel.load()

# Single patient prediction
patient = pd.DataFrame([{
    "age": 72,
    "length_of_stay": 5,
    "num_previous_visits": 3,
    "department_name": "Cardiology",
    "diagnosis_category": "Cardiac",
    "insurance_type": "Medicare",
    "admission_date": "2024-01-15",
}])

risk = readmission_model.predict_proba(patient)[0]
los = los_model.predict(patient)[0]

print(f"Readmission risk: {risk:.1%}")
print(f"Predicted LOS: {los:.1f} days")
```

## Feature Engineering

| Feature | Type | Description |
|---------|------|-------------|
| `age` | numeric | Patient age in years |
| `length_of_stay` | numeric | Days admitted (readmission model only) |
| `num_previous_visits` | numeric | Prior encounters for same patient |
| `department_encoded` | encoded | Department name → integer |
| `diagnosis_severity` | ordinal 1-5 | Cardiac=5, General=2 |
| `insurance_encoded` | encoded | Insurance type → integer |
| `admission_hour` | numeric | Hour of admission (LOS model only) |

## Directory Structure

```
ml/
├── models/
│   ├── readmission_model.py   # ReadmissionRiskModel class
│   └── los_model.py           # LOSPredictionModel class
├── saved_models/              # Persisted joblib artifacts (gitignored)
├── train_models.py            # Training script
└── README.md
```
