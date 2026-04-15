from __future__ import annotations

import pandas as pd


def build_feature_table(dataset: pd.DataFrame, horizon_minutes: int = 120) -> pd.DataFrame:
    if dataset.empty:
        return dataset.copy()

    df = dataset.copy().sort_values(["station_id", "collected_at"])
    df["hour"] = df["collected_at"].dt.hour
    df["day_of_week"] = df["collected_at"].dt.dayofweek
    df["is_weekend"] = df["day_of_week"].isin([5, 6]).astype(int)
    capacity = df["capacity"].replace(0, pd.NA)
    df["occupancy_rate"] = (df["num_bikes_available"] / capacity).fillna(0.0)

    steps = max(1, horizon_minutes // 5)
    for lag in (1, 3, 6):
        df[f"bikes_lag_{lag}"] = df.groupby("station_id")["num_bikes_available"].shift(lag)
        df[f"docks_lag_{lag}"] = df.groupby("station_id")["num_docks_available"].shift(lag)

    df["target_bikes_2h"] = df.groupby("station_id")["num_bikes_available"].shift(-steps)
    df["target_docks_2h"] = df.groupby("station_id")["num_docks_available"].shift(-steps)

    numeric_cols = [
        "num_bikes_available", "num_docks_available", "num_ebikes_available", "mechanical_bikes",
        "occupancy_rate", "bikes_lag_1", "bikes_lag_3", "bikes_lag_6", "docks_lag_1", "docks_lag_3", "docks_lag_6",
        "target_bikes_2h", "target_docks_2h",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.dropna(subset=["target_bikes_2h"]).reset_index(drop=True)
