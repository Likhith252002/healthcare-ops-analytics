"""
Length of Stay (LOS) Prediction Model

Predicts expected inpatient length of stay (in days) using patient and encounter features.
"""
import numpy as np
import pandas as pd
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import LabelEncoder


FEATURES = [
    "age",
    "num_previous_visits",
    "department_encoded",
    "diagnosis_severity",
    "insurance_encoded",
    "admission_hour",
]

MODEL_PATH = Path(__file__).parent.parent / "saved_models" / "los_model.joblib"
ENCODER_PATH = Path(__file__).parent.parent / "saved_models" / "los_encoders.joblib"


class LOSPredictionModel:
    """Random Forest regressor for inpatient length-of-stay prediction (days)."""

    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
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
        df["num_previous_visits"] = df["num_previous_visits"].fillna(0).clip(lower=0)

        if "admission_date" in df.columns:
            df["admission_hour"] = pd.to_datetime(
                df["admission_date"], errors="coerce"
            ).dt.hour.fillna(12)
        else:
            df["admission_hour"] = 12

        return df[FEATURES]

    def train(self, df: pd.DataFrame, target_col: str = "length_of_stay") -> dict:
        """
        Train the LOS model.

        Args:
            df: DataFrame with features + target column
            target_col: Continuous target in days (clipped to 0-60)

        Returns:
            dict with MAE, RMSE, R², feature importances
        """
        df = df.copy()
        df[target_col] = df[target_col].clip(lower=0, upper=60)

        X = self.prepare_features(df, fit=True)
        y = df[target_col].astype(float)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        self.model.fit(X_train, y_train)
        self.is_trained = True

        y_pred = self.model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        feature_importance = dict(
            zip(FEATURES, self.model.feature_importances_.round(4))
        )

        metrics = {
            "mae": round(mae, 4),
            "rmse": round(rmse, 4),
            "r2": round(r2, 4),
            "feature_importance": feature_importance,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
        }

        print(f"LOS Model — MAE: {mae:.2f} days | RMSE: {rmse:.2f} days | R²: {r2:.4f}")
        print("Feature Importances:")
        for feat, imp in sorted(feature_importance.items(), key=lambda x: -x[1]):
            print(f"  {feat}: {imp:.4f}")

        return metrics

    def predict(self, df: pd.DataFrame) -> np.ndarray:
        """Return predicted length of stay in days."""
        if not self.is_trained:
            raise RuntimeError("Model must be trained or loaded before predicting.")
        X = self.prepare_features(df, fit=False)
        predictions = self.model.predict(X)
        return np.clip(predictions, 0, None)

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
    ) -> "LOSPredictionModel":
        """Load a previously saved model from disk."""
        instance = cls()
        instance.model = joblib.load(model_path)
        encoders = joblib.load(encoder_path)
        instance.dept_encoder = encoders["dept_encoder"]
        instance.insurance_encoder = encoders["insurance_encoder"]
        instance.is_trained = True
        return instance
