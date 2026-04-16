import pandas as pd
from pathlib import Path

import psycopg2
import psycopg2.extras
import os

DATA_PATH = Path("data/processed/predictions.csv")
from dotenv import load_dotenv
load_dotenv()

def extrat_postgres_data():


    try:
        print( f" message {os.getenv("PG_Login")}")
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
                 station_id,
                 num_docks_available,
                 num_bikes_mechanical,
                 num_bikes_ebike,
                 num_bikes_available,
                 capacity,
                 collected_at,
                 hour,
                 day_of_week,
                 prediction

            FROM predictions_velib
        """
        
        # 3. Chargement dans Pandas
        # On utilise le bloc 'with' pour s'assurer que la connexion se ferme
        df = pd.read_sql_query(query, conn)
        print(df.columns)

        return df
    except Exception as e:
        print(f"Erreur de connexion ou de requête : {e}")
        return None
    finally:
        if 'conn' in locals():
            conn.close()
    

def main():
    print("Loading data...")
    df = pd.read_csv(DATA_PATH)
    df = extrat_postgres_data() 
    #print("\n=== KPI GLOBAL ===")
    #print(f"Nb lignes : {len(df)}")

    avg_bikes = df["num_bikes_available"].mean()
    print(f"Moyenne vélos disponibles : {avg_bikes:.2f}")

    print("\n=== STATIONS VIDES ===")
    empty = df[df["num_bikes_available"] == 0]
    #print(empty[["station_id", "name"]])
    print(empty[["station_id"]])


    print("\n=== STATIONS PLEINES ===")
    full = df[df["num_docks_available"] == 0]
    print(full[["station_id"]])

    print("\n=== TOP RISQUE (prediction faible) ===")
    critical = df.sort_values("prediction").head(5)
    print(critical[["station_id", "prediction"]])


if __name__ == "__main__":
    main()