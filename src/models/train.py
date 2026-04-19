from pathlib import Path
import pandas as pd
import joblib
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error

import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
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
                s.inserted_at as collected_at
            FROM station_status_flat s
            JOIN station_info_flat i ON s.station_id = i.station_id;
        """
        
        # Avec SQLAlchemy, Pandas gère l'ouverture/fermeture seul
        df = pd.read_sql_query(query, engine)
        return df

    except Exception as e:
        print(f"Erreur lors de l'extraction : {e}")
        return None








def main():
    print("1) Chargement des données...")

    
    #df = pd.read_csv(DATA_PATH)
    df = extract_postgres_data()

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