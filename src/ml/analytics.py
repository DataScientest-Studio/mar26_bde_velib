from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import pandas as pd

from config import settings


@dataclass(slots=True)
class StationRisk:
    station_id: str
    station_name: str
    bikes_available: int
    docks_available: int
    occupancy_rate: float
    criticality_score: float


def compute_network_availability(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    latest = df.sort_values("collected_at").groupby("station_id").tail(1)
    available = ((latest["num_bikes_available"] > 0) & (latest["num_docks_available"] > 0)).mean()
    return round(float(available) * 100, 2)


def top_critical_stations(df: pd.DataFrame, limit: int = 20) -> list[StationRisk]:
    if df.empty:
        return []
    latest = df.sort_values("collected_at").groupby("station_id").tail(1).copy()
    latest["occupancy_rate"] = (latest["num_bikes_available"] / latest["capacity"].replace(0, pd.NA)).fillna(0.0)
    latest["criticality_score"] = (
        latest["num_bikes_available"].le(settings.alert_threshold_bikes).astype(int) * 3
        + latest["num_docks_available"].le(settings.alert_threshold_docks).astype(int) * 3
        + (1 - latest["occupancy_rate"].clip(0, 1))
    )
    ordered = latest.sort_values(["criticality_score", "num_bikes_available", "num_docks_available"], ascending=[False, True, True]).head(limit)
    result: list[StationRisk] = []
    for row in ordered.itertuples(index=False):
        result.append(
            StationRisk(
                station_id=str(row.station_id),
                station_name=getattr(row, "name", str(row.station_id)),
                bikes_available=int(row.num_bikes_available),
                docks_available=int(row.num_docks_available),
                occupancy_rate=round(float(row.occupancy_rate), 3),
                criticality_score=round(float(row.criticality_score), 3),
            )
        )
    return result


def build_stats_payload(df: pd.DataFrame) -> dict[str, Any]:
    latest = df.sort_values("collected_at").groupby("station_id").tail(1) if not df.empty else df
    return {
        "network_availability_rate": compute_network_availability(df),
        "stations_count": int(latest["station_id"].nunique()) if not latest.empty else 0,
        "bikes_available_total": int(latest["num_bikes_available"].sum()) if not latest.empty else 0,
        "docks_available_total": int(latest["num_docks_available"].sum()) if not latest.empty else 0,
        "critical_stations": [asdict(item) for item in top_critical_stations(df)],
    }
