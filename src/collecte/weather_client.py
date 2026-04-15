from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json
from typing import Any

import requests

from config import settings


class WeatherApiError(RuntimeError):
    pass


def fetch_weather_forecast(latitude: float | None = None, longitude: float | None = None) -> dict[str, Any]:
    params = {
        "latitude": latitude or settings.default_latitude,
        "longitude": longitude or settings.default_longitude,
        "hourly": "temperature_2m,precipitation,wind_speed_10m",
        "forecast_days": 2,
    }
    try:
        response = requests.get(settings.weather_api_url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise WeatherApiError(f"Erreur API météo: {exc}") from exc


def save_weather_snapshot(payload: dict[str, Any], output_dir: Path | None = None) -> Path:
    target_dir = output_dir or settings.raw_dir / "weather"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path
