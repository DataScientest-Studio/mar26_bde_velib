from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from config import settings
from ml.train_model import FEATURE_COLUMNS


class PredictionError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def load_model(model_path: Path | None = None) -> dict[str, Any]:
    path = model_path or settings.model_dir / "random_forest_bikes_2h.joblib"
    if not path.exists():
        raise PredictionError(f"Artefact modèle introuvable: {path}")
    return joblib.load(path)


def predict(input_data: dict[str, Any]) -> float:
    bundle = load_model()
    pipeline = bundle["pipeline"]
    feature_columns = bundle.get("feature_columns", FEATURE_COLUMNS)
    row = {column: input_data.get(column) for column in feature_columns}
    missing = [column for column in feature_columns if row[column] is None]
    if missing:
        raise PredictionError(f"Variables manquantes pour la prédiction: {', '.join(missing)}")
    frame = pd.DataFrame([row])
    prediction = pipeline.predict(frame)[0]
    return max(0.0, float(prediction))
