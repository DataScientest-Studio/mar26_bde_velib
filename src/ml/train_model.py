from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_squared_error
from sklearn.pipeline import Pipeline

from config import settings
from data.make_dataset import build_dataset
from features.build_features import build_feature_table

FEATURE_COLUMNS = [
    "hour", "day_of_week", "is_weekend", "capacity", "occupancy_rate",
    "num_bikes_available", "num_docks_available", "num_ebikes_available", "mechanical_bikes",
    "bikes_lag_1", "bikes_lag_3", "bikes_lag_6", "docks_lag_1", "docks_lag_3", "docks_lag_6",
]


@dataclass(slots=True)
class TrainingArtifacts:
    model_path: Path
    metrics_path: Path
    rmse: float
    rows_train: int
    rows_test: int


def _time_split(df: pd.DataFrame, test_ratio: float = 0.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    split_idx = max(1, int(len(df) * (1 - test_ratio)))
    return df.iloc[:split_idx].copy(), df.iloc[split_idx:].copy()


def train_random_forest(dataset: pd.DataFrame | None = None) -> TrainingArtifacts:
    if dataset is None:
        dataset = build_dataset()
    features_df = build_feature_table(dataset)
    if features_df.empty:
        raise ValueError("Dataset insuffisant pour entraîner le modèle.")

    train_df, test_df = _time_split(features_df)
    X_train = train_df[FEATURE_COLUMNS]
    y_train = train_df["target_bikes_2h"]
    X_test = test_df[FEATURE_COLUMNS]
    y_test = test_df["target_bikes_2h"]

    preprocessor = ColumnTransformer(
        transformers=[("num", Pipeline([("imputer", SimpleImputer(strategy="median"))]), FEATURE_COLUMNS)],
        remainder="drop",
    )
    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", RandomForestRegressor(n_estimators=250, random_state=42, min_samples_leaf=2, n_jobs=-1)),
        ]
    )
    pipeline.fit(X_train, y_train)
    predictions = pipeline.predict(X_test)
    rmse = float(mean_squared_error(y_test, predictions, squared=False))

    settings.model_dir.mkdir(parents=True, exist_ok=True)
    model_path = settings.model_dir / "random_forest_bikes_2h.joblib"
    metrics_path = settings.model_dir / "metrics.json"
    joblib.dump({"pipeline": pipeline, "feature_columns": FEATURE_COLUMNS}, model_path)
    metrics_path.write_text(json.dumps({"rmse": rmse, "rows_train": len(train_df), "rows_test": len(test_df)}, indent=2), encoding="utf-8")

    return TrainingArtifacts(model_path=model_path, metrics_path=metrics_path, rmse=rmse, rows_train=len(train_df), rows_test=len(test_df))


if __name__ == "__main__":
    artifacts = train_random_forest()
    print(f"Modèle sauvegardé: {artifacts.model_path} | RMSE={artifacts.rmse:.3f}")
