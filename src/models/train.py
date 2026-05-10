from pathlib import Path
import pandas as pd
import joblib
import numpy as np
import os
import sys
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
from dotenv import load_dotenv
import psutil
import lightgbm as lgb


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger

logger = setup_logger()
load_dotenv()



MODEL_PATH = Path("models/model.pkl")
MODEL_PATH2 = Path("models/LGBMRegressor.pkl")

def train_random_forest ( X_train, X_test, y_train, y_test ) :

    model = RandomForestRegressor(n_estimators=100, random_state=42 , max_depth=20 , n_jobs= 12 , verbose= 1 , max_samples = 0.1 )
    model.fit(X_train, y_train)
    print(f"Score train : {model.score(X_train, y_train):.4f}")
    print(f"Score test  : {model.score(X_test, y_test):.4f}")

    
    rmse = root_mean_squared_error(y_test, model.predict(X_test))

    print(f"RMSE = {rmse:.4f}")

    return model

def train_LGBMRegressor ( X_train, X_test, y_train, y_test ) :

    model = lgb.LGBMRegressor(n_estimators=500)
    model.fit(X_train, y_train)
    print(f"Score train : {model.score(X_train, y_train):.4f}")
    print(f"Score test  : {model.score(X_test, y_test):.4f}")

    
    rmse = root_mean_squared_error(y_test, model.predict(X_test))

    print(f"RMSE = {rmse:.4f}")

    return model



def main():
    logger.info("Lancement entrainement du modèle...")
    logger.info("Chargement des données...")
    df = PostgreRequest.extract_postgres_data_training()

    ram = psutil.virtual_memory()
    logger.info(f"RAM disponible : {ram.available / 1e9:.1f} GB / {ram.total / 1e9:.1f} GB")
    logger.info(f"Taille df en mémoire : {df.memory_usage(deep=True).sum() / 1e9:.2f} GB")

    if df.empty:
        raise ValueError("Dataset vide")

    # ── Feature engineering ─────────────────────────────
    logger.info("Feature engineering...")

    weather_map = {
        "ciel dégagé": 0, "peu nuageux": 1,
        "partiellement nuageux": 2, "couvert": 3,
        "nuageux": 4, "légère pluie": 5,
        "pluie": 6, "orage": 7,
        "neige": 8, "brume": 9
    }
    df["description_code"] = df["description"].map(weather_map).fillna(-1)
    df["collected_at"] = pd.to_datetime(df["collected_at"])

    h = df["collected_at"].dt.hour
    m = df["collected_at"].dt.minute

    
    df["hour_sin"]    = np.sin(2 * np.pi * h / 24)
    df["hour_cos"]    = np.cos(2 * np.pi * h / 24)
    df["min_sin"]     = np.sin(2 * np.pi * m / 60)
    df["min_cos"]     = np.cos(2 * np.pi * m / 60)
    df["day_of_week"] = df["collected_at"].dt.dayofweek

    # ── Target ──────────────────────────────────────────
    df = df[df["capacity"] > 0].copy()
    df["target_pct"] = df["num_bikes_available"] / df["capacity"]





    df = df.sort_values(["id_station", "collected_at"]).reset_index(drop=True)

    #df["lag_10min"] = df.groupby("id_station")["target_pct"].shift(1)
    #df["lag_1h"]    = df.groupby("id_station")["target_pct"].shift(6)
    df["lag_24h"]   = df.groupby("id_station")["target_pct"].shift(144)
    df["lag_7j"]    = df.groupby("id_station")["target_pct"].shift(1008)

    """
    df["rolling_1h"] = (
        df.groupby("id_station")["target_pct"]
        .transform(lambda x: x.shift(1).rolling(6, min_periods=1).mean())
    )
    df = df.dropna(subset=["lag_10min"])

    """



    FEATURES = [
        "id_station", "hour_sin", "hour_cos",
        "min_sin", "min_cos", "day_of_week",
        "temp", "humidity", "wind_speed",
        "description_code", "capacity" ,


         "lag_24h", "lag_7j"
    ]

    # ── Split chronologique ──────────────────────────────
    logger.info("Split chronologique...")
    df = df.sort_values("collected_at").reset_index(drop=True)
    split_idx = int(len(df) * 0.80)

    train_df = df.iloc[:split_idx]
    test_df  = df.iloc[split_idx:]

    print( f" train_df  max {train_df["collected_at"].max()} " )
    print( f" train_df  min {train_df["collected_at"].min()} " )


    print( f" train_df  max {train_df["collected_at"].max().strftime("%A")} " )
    print( f" train_df  min {train_df["collected_at"].min().strftime("%A")}  " )

    print(df["collected_at"].min())
    print(df["collected_at"].max())
    print(df.shape)


    print(f"train max : {train_df['collected_at'].max()}")
    print(f"test  min : {test_df['collected_at'].min()}")
    print(f"test  max : {test_df['collected_at'].max()}")

    assert train_df["collected_at"].max() <= test_df["collected_at"].min(), \
        "❌ Chevauchement entre train et test !"
    logger.info("✅ Pas de chevauchement")

    # Sample sécurisé
    n_train = min(20_000_000, len(train_df))
    n_test  = min(5_000_000,  len(test_df))
    train_df = train_df.sample(n=n_train, random_state=42)
    test_df  = test_df.sample(n=n_test,  random_state=42)

    X_train, y_train = train_df[FEATURES], train_df["target_pct"]
    X_test,  y_test  = test_df[FEATURES],  test_df["target_pct"]

    # ── Logs stats ───────────────────────────────────────
    logger.info("=" * 50)
    logger.info(f"Train : {len(train_df)} lignes | {train_df['collected_at'].min()} → {train_df['collected_at'].max()}")
    logger.info(f"Test  : {len(test_df)}  lignes | {test_df['collected_at'].min()} → {test_df['collected_at'].max()}")


    logger.info(f"Target train → mean: {y_train.mean():.4f} | std: {y_train.std():.4f}")
    logger.info(f"Target test  → mean: {y_test.mean():.4f}  | std: {y_test.std():.4f}")

    # ── Entraînement ─────────────────────────────────────
    logger.info("Entraînement...")
    model = train_random_forest(X_train, X_test, y_train, y_test)
    LGBMRegressor = train_LGBMRegressor(X_train, X_test, y_train, y_test)
    
    # ── Sauvegarde ───────────────────────────────────────
    logger.info("Sauvegarde modèle...")
    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    logger.info(f"Model saved -> {MODEL_PATH}")


    MODEL_PATH2.parent.mkdir(exist_ok=True)
    joblib.dump(LGBMRegressor, MODEL_PATH2)
    logger.info(f"Model saved -> {MODEL_PATH2}")



if __name__ == "__main__":
    main()