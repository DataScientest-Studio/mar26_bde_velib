from __future__ import annotations

import pandas as pd
from fastapi.testclient import TestClient
import joblib
from sklearn.dummy import DummyRegressor
from sklearn.pipeline import Pipeline

from api.main import app
from config import settings


def _ensure_model() -> None:
    settings.model_dir.mkdir(parents=True, exist_ok=True)
    model_path = settings.model_dir / "random_forest_bikes_2h.joblib"
    pipeline = Pipeline([("model", DummyRegressor(strategy="constant", constant=7.0))])
    pipeline.fit(pd.DataFrame([[0] * 15]), [7.0])
    joblib.dump({"pipeline": pipeline, "feature_columns": [
        "hour", "day_of_week", "is_weekend", "capacity", "occupancy_rate",
        "num_bikes_available", "num_docks_available", "num_ebikes_available", "mechanical_bikes",
        "bikes_lag_1", "bikes_lag_3", "bikes_lag_6", "docks_lag_1", "docks_lag_3", "docks_lag_6",
    ]}, model_path)


def _ensure_dataset() -> None:
    settings.processed_dir.mkdir(parents=True, exist_ok=True)
    dataset_path = settings.processed_dir / "velib_dataset.csv"
    pd.DataFrame([
        {"station_id": "A", "name": "Station A", "capacity": 20, "num_bikes_available": 5, "num_docks_available": 15, "collected_at": pd.Timestamp("2026-04-15T08:00:00Z")},
        {"station_id": "B", "name": "Station B", "capacity": 20, "num_bikes_available": 0, "num_docks_available": 20, "collected_at": pd.Timestamp("2026-04-15T08:00:00Z")},
    ]).to_csv(dataset_path, index=False)


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_predict() -> None:
    _ensure_model()
    client = TestClient(app)
    payload = {
        "station_id": "A",
        "hour": 8,
        "day_of_week": 1,
        "is_weekend": 0,
        "capacity": 20,
        "occupancy_rate": 0.25,
        "num_bikes_available": 5,
        "num_docks_available": 15,
        "num_ebikes_available": 2,
        "mechanical_bikes": 3,
        "bikes_lag_1": 5,
        "bikes_lag_3": 5,
        "bikes_lag_6": 5,
        "docks_lag_1": 15,
        "docks_lag_3": 15,
        "docks_lag_6": 15,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    assert response.json()["station_id"] == "A"


def test_stats() -> None:
    _ensure_dataset()
    client = TestClient(app)
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["stations_count"] == 2
    assert isinstance(data["critical_stations"], list)
