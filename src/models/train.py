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

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger

logger = setup_logger()
load_dotenv()

MODEL_PATH = Path("models/model.pkl")


def Model_RandomForest ( X_train, X_test, y_train, y_test ) :

    model = RandomForestRegressor(n_estimators=100, random_state=42 , max_depth=20 , n_jobs= 8 , verbose= 1 )
    model.fit(X_train, y_train)
    print(f"Score train : {model.score(X_train, y_train):.4f}")
    print(f"Score test  : {model.score(X_test, y_test):.4f}")

    
    rmse = root_mean_squared_error(y_test, model.predict(X_test))

    print(f"RMSE = {rmse:.4f}")

    return model



def main():
    logger.info("Lancement entrainement du modèle...")
    logger.info("Chargement des données...")
    #print("1) Chargement des données...")

    
    #df = pd.read_csv(DATA_PATH)
    #df = extract_postgres_data()
    df = PostgreRequest.extract_postgres_data_training()

    print(f"   shape = {df.shape}")
    print(f"   colonnes = {list(df.columns)}")

    if df.empty:
        raise ValueError("Dataset vide")

    logger.info("Feature engineering...")
    #print("2) Feature engineering...")


    weather_map = {
            "ciel dégagé": 0,
            "peu nuageux" : 1 ,
            "partiellement nuageux" :2 ,
            "couvert": 3 ,
            "nuageux" : 4 ,
            "légère pluie" : 5,
            "pluie" : 6 ,
            "orage" : 7 ,            
            "neige" : 8 ,
            "brume" : 9
            }
    
    df['description_code'] = df['description'].map(weather_map).fillna(-1)
    
    df['description_code'].head()

    df["collected_at"] = pd.to_datetime(df["collected_at"])

    df["hour"] = df["collected_at"].dt.hour
    df["minute"] = df["collected_at"].dt.minute
    df["day_of_week"] = df["collected_at"].dt.dayofweek



    h = df["collected_at"].dt.hour
    m = df["collected_at"].dt.minute

    df["hour_sin"] = np.sin(2 * np.pi * h / 24)
    df["hour_cos"] = np.cos(2 * np.pi * h / 24)
    df["min_sin"] = np.sin(2 * np.pi * m / 60)
    df["min_cos"] = np.cos(2 * np.pi * m / 60)


    logger.info("Préparation des variables...")
    #print("3) Préparation des variables...")
    df = df[df["capacity"] > 0].copy()
    df["target_pct"] = df["num_bikes_available"] / df["capacity"]

    #X = df[["station_id", "hour", "minute" , "day_of_week", 'temp', "humidity", "wind_speed", "description_code", "capacity" ]]

    X = df[ [ "id_station", "hour_sin","hour_cos", "min_sin", "min_cos", "day_of_week", "temp", "humidity","wind_speed", "description_code","capacity" ] ]
    y = df["target_pct"]


    
    print(f"   X.shape = {X.shape}")
    logger.info("Entraînement..")
    print("4) Entraînement...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20)

    model = Model_RandomForest(X_train, X_test, y_train, y_test )

    logger.info("Sauvegarde modèle...")
    print("5) Sauvegarde modèle...")


    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Model saved -> {MODEL_PATH}")
    logger.info(f"Model saved -> {MODEL_PATH}")

if __name__ == "__main__":
    main()