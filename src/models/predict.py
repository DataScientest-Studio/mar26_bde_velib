from pathlib import Path
import pandas as pd
import joblib


import psycopg2
import psycopg2.extras
import pandas as pd


from sqlalchemy import create_engine
import os
import sys
from dotenv import load_dotenv
load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger 
logger = setup_logger()

MODEL_PATH = Path("models/model.pkl")
DATA_PATH = Path("data/processed/velib_dataset.csv")


def create_table() -> None:

    """
    Creation de la table predictions_velib dans PostgreSQL
    
    """

    pg_conn = psycopg2.connect(
            database="db_velib",
            user=os.getenv("PG_LOGIN"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
        )
    

    with pg_conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS predictions_velib (
                id                  SERIAL PRIMARY KEY,
                station_id          BIGINT NOT NULL,
                num_docks_available INT,
                num_bikes_mechanical INT,
                num_bikes_ebike     INT,
                num_bikes_available     INT,
                capacity            INT,
                collected_at        TIMESTAMPTZ DEFAULT NOW(),
                hour                int ,
                day_of_week         INT ,
                prediction          INT
            );
                    


        """)
    pg_conn.commit()



def extrat_postgres_data():


    try:
        conn = psycopg2.connect(
            database="db_velib",
            user=os.getenv("PG_LOGIN"),
            password=os.getenv("PG_PASSWORD"),
            host=os.getenv("PG_HOST"),
            port=os.getenv("PG_PORT")
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
            JOIN station_info_flat i ON s.station_id = i.station_id
            where s.inserted_at = (SELECT inserted_at from station_status_flat ORDER BY inserted_at DESC LIMIT 1)
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
    df = PostgreRequest.extract_postgres_data_training()
    #df = extrat_postgres_data()

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


    user = os.getenv("PG_LOGIN")
    password = os.getenv("PG_PASSWORD")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")
    db = "db_velib"


    create_table()
    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}')
    df.to_sql('predictions_velib', engine, if_exists='append', index=False)
    print("Predictions saved in PostgreSQL table: predictions_velib")



    print(df.head())
    os.makedirs('data/processed', exist_ok=True)
    out_path = Path("data/processed/predictions.csv")
    df.to_csv(out_path, index=False)

    print(f"Predictions saved -> {out_path}")


if __name__ == "__main__":
    main()