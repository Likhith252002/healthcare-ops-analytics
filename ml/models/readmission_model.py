"""
Readmission Risk Prediction Model

Predicts 30-day hospital readmission probability using patient and encounter features.
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, classification_report
from sklearn.preprocessing import LabelEncoder


FEATURES = [
    "age",
    "length_of_stay",
    "num_previous_visits",
    "department_encoded",
    "diagnosis_severity",
    "insurance_encoded",
]

MODEL_PATH = Path(__file__).parent.parent / "saved_models" / "readmission_model.joblib"
ENCODER_PATH = Path(__file__).parent.parent / "saved_models" / "readmission_encoders.joblib"


class ReadmissionRiskModel:
    """Random Forest classifier for 30-day readmission risk prediction."""

    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=20,
            min_samples_leaf=10,
            random_state=42,
            n_jobs=-1,
        )
        self.dept_encoder = LabelEncoder()
        self.insurance_encoder = LabelEncoder()
        self.is_trained = False

    def _encode_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Encode categorical features."""
        df = df.copy()

        if fit:
            df["department_encoded"] = self.dept_encoder.fit_transform(
                df["department_name"].fillna("Unknown")
            )
            df["insurance_encoded"] = self.insurance_encoder.fit_transform(
                df["insurance_type"].fillna("Unknown")
            )
        else:
            df["department_encoded"] = self.dept_encoder.transform(
                df["department_name"].fillna("Unknown")
            )
            df["insurance_encoded"] = self.insurance_encoder.transform(
                df["insurance_type"].fillna("Unknown")
            )

        return df

    def _severity_score(self, diagnosis: pd.Series) -> pd.Series:
        """Map diagnosis categories to severity scores 1-5."""
        severity_map = {
            "Cardiac": 5,
            "Respiratory": 4,
            "Neurological": 4,
            "Orthopedic": 3,
            "Gastrointestinal": 3,
            "Infectious Disease": 4,
            "Endocrine": 3,
            "Renal": 4,
            "Psychiatric": 3,
            "General": 2,
        }
        return diagnosis.map(severity_map).fillna(2).astype(int)

    def prepare_features(self, df: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """Prepare feature matrix from raw encounter data."""
        df = df.copy()
        df["diagnosis_severity"] = self._severity_score(
            df.get("diagnosis_category", pd.Series(["General"] * len(df)))
        )
        df = self._encode_features(df, fit=fit)
        df["age"] = df["age"].fillna(df["age"].median())
        df["length_of_stay"] = df["length_of_stay"].fillna(0).clip(lower=0)
        df["num_previous_visits"] = df["num_previous_visits"].fillna(0).clip(lower=0)
        return df[FEATURES]

    def train(self, df: pd.DataFrame, target_col: str = "readmitted_30d") -> dict:
        """
        Train the readmission model.

        Args:
            df: DataFrame with features + target column
            target_col: Binary target (1 = readmitted within 30 days)

        Returns:
            dict with ROC-AUC, feature importances, classification report
        """
        X = self.prepare_features(df, fit=True)
        y = df[target_col].astype(int)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        y_pred = self.model.predict(X_test)

        roc_auc = roc_auc_score(y_test, y_pred_proba)
        report = classification_report(y_test, y_pred, output_dict=True)

        feature_importance = dict(
            zip(FEATURES, self.model.feature_importances_.round(4))
        )

        metrics = {
            "roc_auc": round(roc_auc, 4),
            "classification_report": report,
            "feature_importance": feature_importance,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        print(f"Readmission Model — ROC-AUC: {roc_auc:.4f}")
        print("Feature Importances:")
        for feat, imp in sorted(feature_importance.items(), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.4f}")

        return metrics

    def predict_proba(self, df: pd.DataFrame) -> np.ndarray:
        """Return readmission probability for each row (0-1)."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained or loaded before predicting.")
        X = self.prepare_features(df, fit=False)
        return self.model.predict_proba(X)[:, 1]

    def predict(self, df: pd.DataFrame, threshold: float = 0.5) -> np.ndarray:
        """Return binary readmission prediction."""
        return (self.predict_proba(df) >= threshold).astype(int)

    def save(self, model_path: Path = MODEL_PATH, encoder_path: Path = ENCODER_PATH):
        """Save model and encoders to disk."""
        model_path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, model_path)
        joblib.dump(
            {
                "dept_encoder": self.dept_encoder,
                "insurance_encoder": self.insurance_encoder,
            },
            encoder_path,
        )
        print(f"Model saved to {model_path}")

    @classmethod
    def load(
        cls, model_path: Path = MODEL_PATH, encoder_path: Path = ENCODER_PATH
    ) -> "ReadmissionRiskModel":
        """Load a previously saved model from disk."""
        instance = cls()
        instance.model = joblib.load(model_path)
        encoders = joblib.load(encoder_path)
        instance.dept_encoder = encoders["dept_encoder"]
        instance.insurance_encoder = encoders["insurance_encoder"]
        instance.is_trained = True
        return instance
