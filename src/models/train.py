from pathlib import Path
import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error
from sklearn.model_selection import train_test_split
import psycopg2
import numpy as np

import os
from dotenv import load_dotenv
load_dotenv()


DATA_PATH = Path("data/processed/velib_dataset.csv")
MODEL_PATH = Path("models/model.pkl")


def extract_postgres_data():
    # Construction de l'URL de connexion (URI)
    user = os.getenv("PG_LOGIN")
    password = os.getenv("PG_PASSWORD")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    dbname = "db_velib"
    
    # Format : postgresql://user:password@host:port/dbname
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    try:
        # Création du moteur SQLAlchemy
        engine = create_engine(connection_string)

        query = """
            SELECT 
                s.station_id, 
                s.num_docks_available, 
                s.num_bikes_mechanical, 
                s.num_bikes_ebike,
                (s.num_bikes_mechanical + s.num_bikes_ebike) as num_bikes_available,
                i.capacity, 
                s.inserted_at as collected_at,
                w.temp, 
                w.humidity, 
                w.wind_speed,
                w.description , 
                w.inserted_at 
            FROM station_status_flat s
            JOIN station_info_flat i ON s.station_id = i.station_id
            LEFT JOIN meteo w ON  DATE_TRUNC('hour', s.inserted_at) = DATE_TRUNC('hour', w.inserted_at)  ;
        """
        
        
        with engine.connect() as conn:
            df = pd.read_sql_query(query, conn)
        return df

    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return None



def Model_RandomForest ( X_train, X_test, y_train, y_test ) :

    model = RandomForestRegressor(n_estimators=100, random_state=42 , max_depth=30 , n_jobs= 10 , verbose= 1 )
    model.fit(X_train, y_train)
    print(f"Score train : {model.score(X_train, y_train):.4f}")
    print(f"Score test  : {model.score(X_test, y_test):.4f}")

    
    rmse = root_mean_squared_error(y_test, model.predict(X_test))

    print(f"RMSE = {rmse:.4f}")

    return model





def main():
    print("1) Chargement des données...")

    
    #df = pd.read_csv(DATA_PATH)
    df = extract_postgres_data()

    print(f"   shape = {df.shape}")
    print(f"   colonnes = {list(df.columns)}")

    if df.empty:
        raise ValueError("Dataset vide")

    print("2) Feature engineering...")


    weather_map = {
            "ciel dégagé": 0,
            "peu nuageux" : 1 ,
            "partiellement nuageux" :2 ,
            "couvert": 3 ,
            "nuageux" : 4 ,
            "averses" : 5,
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



    print("3) Préparation des variables...")
    df = df[df["capacity"] > 0].copy()
    df["target_pct"] = df["num_bikes_available"] / df["capacity"]

    #X = df[["station_id", "hour", "minute" , "day_of_week", 'temp', "humidity", "wind_speed", "description_code", "capacity" ]]

    X = df[ [ "station_id", "hour_sin","hour_cos", "min_sin", "min_cos", "day_of_week", "temp", "humidity","wind_speed", "description_code","capacity" ] ]
    y = df["target_pct"]



    print(f"   X.shape = {X.shape}")

    print("4) Entraînement...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20)

    model = Model_RandomForest(X_train, X_test, y_train, y_test )

    print("5) Sauvegarde modèle...")


    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

    print(f"Model saved -> {MODEL_PATH}")


if __name__ == "__main__":
    main()