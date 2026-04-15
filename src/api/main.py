from __future__ import annotations

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from config import settings
from ml.analytics import build_stats_payload
from ml.predict import PredictionError, predict

app = FastAPI(title="Velib Prediction API", version="0.1.0")


class PredictRequest(BaseModel):
    station_id: str = Field(..., examples=["213688169"])
    hour: int = Field(..., ge=0, le=23)
    day_of_week: int = Field(..., ge=0, le=6)
    is_weekend: int = Field(..., ge=0, le=1)
    capacity: int = Field(..., ge=0)
    occupancy_rate: float = Field(..., ge=0.0, le=1.0)
    num_bikes_available: int = Field(..., ge=0)
    num_docks_available: int = Field(..., ge=0)
    num_ebikes_available: int = Field(..., ge=0)
    mechanical_bikes: int = Field(..., ge=0)
    bikes_lag_1: int = Field(..., ge=0)
    bikes_lag_3: int = Field(..., ge=0)
    bikes_lag_6: int = Field(..., ge=0)
    docks_lag_1: int = Field(..., ge=0)
    docks_lag_3: int = Field(..., ge=0)
    docks_lag_6: int = Field(..., ge=0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/predict")
def predict_endpoint(payload: PredictRequest) -> dict[str, object]:
    try:
        prediction = predict(payload.model_dump())
    except PredictionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"Erreur interne: {exc}") from exc
    return {"station_id": payload.station_id, "predicted_bikes": round(prediction, 2), "horizon": "+2h"}


@app.get("/stats")
def stats_endpoint(arrondissement: int | None = Query(default=None, ge=1, le=20)) -> dict[str, object]:
    dataset_path = settings.processed_dir / "velib_dataset.csv"
    if not dataset_path.exists():
        raise HTTPException(status_code=404, detail="Dataset analytique introuvable. Lancez la collecte puis build_dataset().")
    df = pd.read_csv(dataset_path, parse_dates=["collected_at"])
    if arrondissement is not None and "name" in df.columns:
        mask = df["name"].fillna("").str.contains(f"-{arrondissement}")
        df = df[mask]
    return build_stats_payload(df)
