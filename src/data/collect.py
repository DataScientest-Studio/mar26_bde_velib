from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import requests

DATA_DIR = Path("data/raw")
DATA_DIR.mkdir(parents=True, exist_ok=True)

GBFS_ROOT = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
STATION_STATUS_URL = f"{GBFS_ROOT}/station_status.json"
STATION_INFO_URL = f"{GBFS_ROOT}/station_information.json"

HEADERS = {
    "User-Agent": "mar26_bde_velib/1.0",
    "Accept": "application/json",
}


def fetch_data(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def save_data(data: dict, name: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = DATA_DIR / f"{name}_{timestamp}.json"
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path


def main() -> None:
    print("Collecte Vélib en cours...")

    try:
        status = fetch_data(STATION_STATUS_URL)
        info = fetch_data(STATION_INFO_URL)

        p1 = save_data(status, "station_status")
        p2 = save_data(info, "station_information")

        print(f"OK -> {p1}")
        print(f"OK -> {p2}")

    except requests.exceptions.RequestException as e:
        print("Erreur réseau pendant la collecte.")
        print(f"Détail : {e}")
        print("Teste ces URLs dans ton navigateur :")
        print(STATION_STATUS_URL)
        print(STATION_INFO_URL)


if __name__ == "__main__":
    main()