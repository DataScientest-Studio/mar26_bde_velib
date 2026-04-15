from __future__ import annotations

from pathlib import Path
import json

import pandas as pd

from config import settings


def _extract_station_information(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stations = payload.get("data", {}).get("stations", [])
    df = pd.DataFrame(stations)
    keep = [col for col in ["station_id", "name", "lat", "lon", "capacity"] if col in df.columns]
    return df[keep].drop_duplicates(subset=["station_id"])


def _extract_station_status(path: Path) -> pd.DataFrame:
    payload = json.loads(path.read_text(encoding="utf-8"))
    stations = payload.get("data", {}).get("stations", [])
    df = pd.DataFrame(stations)
    if df.empty:
        return df
    timestamp = path.stem
    df["collected_at"] = pd.to_datetime(timestamp, format="%Y%m%dT%H%M%SZ", utc=True)
    if "num_bikes_available_types" in df.columns:
        ebikes = []
        mechanical = []
        for item in df["num_bikes_available_types"].fillna([]):
            if isinstance(item, list):
                counts = {entry.get("bike_type", "unknown"): entry.get("count", 0) for entry in item}
            else:
                counts = {}
            ebikes.append(counts.get("ebike", 0))
            mechanical.append(counts.get("mechanical", 0))
        df["num_ebikes_available"] = ebikes
        df["mechanical_bikes"] = mechanical
    for col in ["num_bikes_available", "num_docks_available", "num_ebikes_available", "mechanical_bikes"]:
        if col not in df.columns:
            df[col] = 0
    keep = ["station_id", "num_bikes_available", "num_docks_available", "num_ebikes_available", "mechanical_bikes", "collected_at"]
    return df[keep]


def build_dataset(raw_dir: Path | None = None, output_path: Path | None = None) -> pd.DataFrame:
    source = raw_dir or settings.raw_dir
    info_dir = source / "station_information.json"
    status_dir = source / "station_status.json"
    if not info_dir.exists() or not status_dir.exists():
        raise FileNotFoundError("Les snapshots Vélib ne sont pas encore disponibles dans data/raw.")

    info_files = sorted(info_dir.glob("*.json"))
    status_files = sorted(status_dir.glob("*.json"))
    if not info_files or not status_files:
        raise FileNotFoundError("Aucun snapshot JSON trouvé.")

    stations = pd.concat([_extract_station_information(path) for path in info_files], ignore_index=True)
    stations = stations.drop_duplicates(subset=["station_id"], keep="last")
    status = pd.concat([_extract_station_status(path) for path in status_files], ignore_index=True)
    dataset = status.merge(stations, on="station_id", how="left")
    dataset = dataset.sort_values(["station_id", "collected_at"]).reset_index(drop=True)

    target = output_path or settings.processed_dir / "velib_dataset.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    dataset.to_csv(target, index=False)
    return dataset


if __name__ == "__main__":
    build_dataset()
