from pathlib import Path
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error


DATA_PATH = Path("data/processed/velib_dataset.csv")
MODEL_PATH = Path("models/model.pkl")


def main():
    print("1) Chargement des données...")
    df = pd.read_csv(DATA_PATH)

    print(f"   shape = {df.shape}")
    print(f"   colonnes = {list(df.columns)}")

    if df.empty:
        raise ValueError("Dataset vide")

    print("2) Feature engineering...")

    # conversion timestamp
    df["collected_at"] = pd.to_datetime(df["collected_at"])

    df["hour"] = df["collected_at"].dt.hour
    df["day_of_week"] = df["collected_at"].dt.dayofweek

    print("3) Préparation des variables...")

    X = df[["hour", "day_of_week", "capacity"]]
    y = df["num_bikes_available"]

    print(f"   X.shape = {X.shape}")

    print("4) Entraînement...")

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)

    preds = model.predict(X)
    rmse = root_mean_squared_error(y, preds)

    print(f"RMSE = {rmse:.2f}")

    print("5) Sauvegarde modèle...")
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Model saved -> {MODEL_PATH}")


if __name__ == "__main__":
    main()