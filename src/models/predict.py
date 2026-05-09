from pathlib import Path
import pandas as pd
import joblib
import numpy as np
import psycopg2
import psycopg2.extras
import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger

logger = setup_logger(name="prediction")

MODEL_PATH = Path("models/model.pkl")




def appel_prediction(model , station , h , m) :
    try :
        #logger.info("Chargement modèle...")
        #print("1) Chargement modèle...")
        #model = joblib.load(MODEL_PATH)


        logger.info("Chargement données...")
        df = PostgreRequest.extrat_postgres_data(station)

        print(f"   colonnes = {list(df.columns)}")

        if df.empty:
            raise ValueError("Dataset vide")



        logger.info("Feature engineering...")

        df["collected_at"] = pd.to_datetime(df["collected_at"])

        df["hour"] = df["collected_at"].dt.hour
        #h = df["collected_at"].dt.hour
        #m = df["collected_at"].dt.minute

        
        df["hour_sin"] = np.sin(2 * np.pi * h / 24)
        df["hour_cos"] = np.cos(2 * np.pi * h / 24)
        df["min_sin"] = np.sin(2 * np.pi * m / 60)
        df["min_cos"] = np.cos(2 * np.pi * m / 60)


        df["day_of_week"] = df["collected_at"].dt.dayofweek


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


        
        logger.info("Prédiction...")
        #print("4) Prédiction...")

        X = df[["id_station", "hour_sin","hour_cos", "min_sin", "min_cos", "day_of_week", "temp", "humidity","wind_speed", "description_code","capacity"]]
        preds =  np.round( model.predict(X) * df['capacity'] )

        df["prediction"] = preds


        return preds
    except Exception as e:
        logger.error( f" Ereeur : {e} ")






if __name__ == "__main__":
    table = []

    model = joblib.load(MODEL_PATH)


    for h in range(21,24):
        for m in range(0, 60, 15):
            
            test = appel_prediction(model , 11218807773, h, m)
            table.append({"hour": f"{h}:{m}", "prediction": test})
            print(f"{h}:{m} - {test}")

    df = pd.DataFrame(table)
    df.head()
