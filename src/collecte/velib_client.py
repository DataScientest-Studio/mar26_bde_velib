from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import json
from typing import Any

import requests

from config import settings


class VelibApiError(RuntimeError):
    """Raised when the Vélib API cannot be reached or parsed."""


@dataclass(slots=True)
class ApiSnapshot:
    endpoint: str
    collected_at: datetime
    payload: dict[str, Any]
    file_path: Path


def _base_session() -> requests.Session:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(max_retries=3)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def fetch_json(endpoint: str, timeout: int = 30) -> dict[str, Any]:
    url = f"{settings.velib_base_url.rstrip('/')}/{endpoint.lstrip('/')}"
    session = _base_session()
    try:
        response = session.get(url, timeout=timeout)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise VelibApiError(f"Erreur API Vélib pour {endpoint}: {exc}") from exc
    except ValueError as exc:
        raise VelibApiError(f"Réponse JSON invalide pour {endpoint}") from exc
    return data


def save_snapshot(endpoint: str, payload: dict[str, Any], output_dir: Path | None = None) -> ApiSnapshot:
    collected_at = datetime.now(UTC)
    target_dir = output_dir or settings.raw_dir / endpoint.replace('/', '_')
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{collected_at.strftime('%Y%m%dT%H%M%SZ')}.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return ApiSnapshot(endpoint=endpoint, collected_at=collected_at, payload=payload, file_path=file_path)


def collect_velib_snapshot() -> dict[str, ApiSnapshot]:
    snapshots: dict[str, ApiSnapshot] = {}
    for endpoint in ("station_information.json", "station_status.json"):
        payload = fetch_json(endpoint)
        snapshots[endpoint] = save_snapshot(endpoint, payload)
    return snapshots
