from pathlib import Path
import pandas as pd
import joblib

MODEL_PATH = Path("models/model.pkl")
DATA_PATH = Path("data/processed/velib_dataset.csv")


def main():
    print("1) Chargement modèle...")
    model = joblib.load(MODEL_PATH)

    print("2) Chargement données...")
    df = pd.read_csv(DATA_PATH)

    print(f"   colonnes = {list(df.columns)}")

    if df.empty:
        raise ValueError("Dataset vide")

    print("3) Feature engineering...")

    df["collected_at"] = pd.to_datetime(df["collected_at"])

    df["hour"] = df["collected_at"].dt.hour
    df["day_of_week"] = df["collected_at"].dt.dayofweek

    print("4) Prédiction...")

    X = df[["hour", "day_of_week", "capacity"]]
    preds = model.predict(X)

    df["prediction"] = preds

    print(df.head())

    out_path = Path("data/processed/predictions.csv")
    df.to_csv(out_path, index=False)

    print(f"Predictions saved -> {out_path}")


if __name__ == "__main__":
    main()