import pandas as pd
from pathlib import Path

DATA_PATH = Path("data/processed/predictions.csv")


def main():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)

    print("\n=== KPI GLOBAL ===")
    print(f"Nb lignes : {len(df)}")

    avg_bikes = df["num_bikes_available"].mean()
    print(f"Moyenne vélos disponibles : {avg_bikes:.2f}")

    print("\n=== STATIONS VIDES ===")
    empty = df[df["num_bikes_available"] == 0]
    print(empty[["station_id", "name"]])

    print("\n=== STATIONS PLEINES ===")
    full = df[df["num_docks_available"] == 0]
    print(full[["station_id", "name"]])

    print("\n=== TOP RISQUE (prediction faible) ===")
    critical = df.sort_values("prediction").head(5)
    print(critical[["station_id", "prediction"]])


if __name__ == "__main__":
    main()