from pathlib import Path
import pandas as pd
import joblib


import psycopg2
import psycopg2.extras

import os
from dotenv import load_dotenv
load_dotenv()


MODEL_PATH = Path("models/model.pkl")
DATA_PATH = Path("data/processed/velib_dataset.csv")


def extrat_postgres_data():


    try:
        conn = psycopg2.connect(
            database="velib",
            user=os.getenv("PG_Login"),
            password=os.getenv("PG_password"),
            host=os.getenv("PG_host"),
            port=os.getenv("PG_port")
        )
        


        # 2. La requête SQL corrigée
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
        
        # 3. Chargement dans Pandas
        # On utilise le bloc 'with' pour s'assurer que la connexion se ferme
        df = pd.read_sql_query(query, conn)
        
        return df

    except Exception as e:
        print(f"Erreur de connexion ou de requête : {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()




def main():
    print("1) Chargement modèle...")
    model = joblib.load(MODEL_PATH)

    print("2) Chargement données...")
    #df = pd.read_csv(DATA_PATH)
    df = extrat_postgres_data()

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
    os.makedirs('data/processed', exist_ok=True)
    out_path = Path("data/processed/predictions.csv")
    df.to_csv(out_path, index=False)

    print(f"Predictions saved -> {out_path}")


if __name__ == "__main__":
    main()