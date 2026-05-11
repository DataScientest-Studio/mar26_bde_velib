from pathlib import Path
import pandas as pd
import joblib
import numpy as np
import psycopg2
import psycopg2.extras
import os
import sys
from dotenv import load_dotenv
import requests
from datetime import datetime, timedelta

load_dotenv()
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger

logger = setup_logger(name="prediction")

MODEL_PATH = Path("models/model.pkl")
model = joblib.load(MODEL_PATH)


FEATURES = [
        "id_station", "hour_sin", "hour_cos",
        "min_sin", "min_cos", "day_of_week",
        "temp", "humidity", "wind_speed",
        "description_code", "capacity" ,


         "lag_24h", "lag_7j"
    ]



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

        df["target_pct"] = df["num_bikes_available"] / df["capacity"]
        df["lag_24h"]   = df.groupby("id_station")["target_pct"].shift(144)
        df["lag_7j"]    = df.groupby("id_station")["target_pct"].shift(1008)

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

        X = df[FEATURES]
        preds =  np.round( model.predict(X) * df['capacity'] )

        df["prediction"] = preds

        return preds
    except Exception as e:
        logger.error( f" Ereeur : {e} ")

def prediction_meteo( longetude , latitude  , heures , date ) :

    url = f'https://api.openweathermap.org/data/2.5/forecast?appid=f8b14f4fcf6c786e41d58b7fd8c32932&units=metric&lang=fr&lat={latitude}&lon={longetude}'
    response = requests.get(url,    timeout=10)

    print(url)
    data = response.json() 
    predictions = data['list']
    resultats = []
    for prediction in predictions:

        date_prediction = datetime.strptime(prediction['dt_txt'], "%Y-%m-%d %H:%M:%S")

        for heure in heures :
            date_demande = datetime.strptime(f"{date} {heure}", "%Y-%m-%d %H:%M")

            date_fin     = date_demande + timedelta(hours=2, minutes=59)
            """
            print(f"date_demande {date_demande}")
            print(f"date_prediction {date_prediction}")
            print(f"date_fin {date_fin}")
            """

            if date_demande <= date_prediction <= date_fin:
                """
                print(prediction['dt_txt'])
                print(prediction['main']['temp'])
                print(prediction['weather'][0]['description'])
                """

                resultats.append({         
                    'date': date , 
                    'heure' : heure,             
                    'temp': prediction['main']['temp'], 
                    'humidity': prediction['main']['humidity'],   
                    'wind_speed': prediction['wind']['speed'],      
                    'description': prediction['weather'][0]['description']
                })

    return resultats


def prediction_station(idstation, heures, date):

    if isinstance(idstation, int):
        idstation = [idstation]

    sortie_prediction = []
    print(f"stations {idstation}")

    # ============================
    # 1️⃣ Info Stations (1 seule requête)
    # ============================
    ids_str = ','.join(map(str, idstation))
    info_stations = PostgreRequest.extrat_info_station(ids_str)

    if not isinstance(info_stations, pd.DataFrame):
        df_station = pd.DataFrame(info_stations)
    else:
        df_station = info_stations.copy()

    # ============================
    # 2️⃣ Données Postgres (1 seule requête)
    # ============================
    ids_str = ','.join(map(str, idstation))
    #postgres_data = PostgreRequest.extrat_postgres_data(ids_str)
    postgres_data = PostgreRequest.extrat_postgres_data_pre(ids_str)
     

    if not isinstance(postgres_data, pd.DataFrame):
        df_postgres = pd.DataFrame(postgres_data)
    else:
        df_postgres = postgres_data.copy()

    print(f"📌 Colonnes info_station  ({df_station.shape})  : {df_station.columns.tolist()}")
    print(f"📌 Colonnes postgres_data ({df_postgres.shape}) : {df_postgres.columns.tolist()}")

    # ============================
    # 3️⃣ Prédiction Météo (1 requête par station car coords différentes)
    # ============================
    resultats_meteo = []

    for _, row in df_station.iterrows():
        meteo = prediction_meteo(
            row["longitude"],
            row["latitude"],
            heures,
            date
        )
        if not isinstance(meteo, pd.DataFrame):
            df_meteo = pd.DataFrame(meteo)
        else:
            df_meteo = meteo.copy()

        df_meteo["id_station"] = row["id_station"]
        resultats_meteo.append(df_meteo)

    df_meteo_all = pd.concat(resultats_meteo, ignore_index=True)

    print(f"📌 Colonnes meteo ({df_meteo_all.shape}) : {df_meteo_all.columns.tolist()}")

    # ============================
    # 🔗 Fusion 1 : station + postgres
    # ============================
    try:
        df_fusion_1 = df_station.merge(
            df_postgres,
            on="id_station",
            how="outer",
            suffixes=("_station", "")
        )
        print("✅ Merge station + postgres réussi")
    except Exception as e:
        print(f"⚠️ Merge station + postgres échoué ({e}), cross join...")
        df_fusion_1 = df_station.merge(df_postgres, how="cross")

    # ============================
    # 🔗 Fusion 2 : (station + postgres) + meteo
    # ============================
    try:



        df_final = df_fusion_1.merge(
            df_meteo_all,
            on="id_station",
            how="inner",
            suffixes=("", "_meteo")
        )
        print("✅ Merge + meteo réussi")
    except Exception as e:
        print(f"⚠️ Merge + meteo échoué ({e}), cross join...")
        df_final = df_fusion_1.merge(df_meteo_all, how="cross")



    print(f"\n{'='*50}")
    print(f"✅ DataFrame FINAL : {df_final.shape[0]} lignes x {df_final.shape[1]} colonnes")
    print(f"📌 Colonnes : {df_final.columns.tolist()}")
    print(df_final.head())

    try:
        logger.info("Chargement données...")

        # ============================
        # ✅ Feature Engineering
        # ============================
        logger.info("Feature engineering...")

        df_final["collected_at"] = pd.to_datetime(df_final["collected_at"])
        df_final["hour"]         = df_final["collected_at"].dt.hour
        df_final["day_of_week"]  = df_final["collected_at"].dt.dayofweek
        
        df_final["hour_meteo"] = df_final["heure"].apply(lambda x: int(str(x).split(':')[0]))
        df_final["min_meteo"]  = df_final["heure"].apply(lambda x: int(str(x).split(':')[1]))

        df_final["hour_sin"] = np.sin(2 * np.pi * df_final["hour_meteo"] / 24)
        df_final["hour_cos"] = np.cos(2 * np.pi * df_final["hour_meteo"] / 24)
        df_final["min_sin"]  = np.sin(2 * np.pi * df_final["min_meteo"]  / 60)
        df_final["min_cos"]  = np.cos(2 * np.pi * df_final["min_meteo"]  / 60)

        df_final["target_pct"] = df_final["num_bikes_available"] / df_final["capacity"]
        #df_final["lag_24h"]    = df_final.groupby("id_station")["target_pct"].shift(144)
        #df_final["lag_7j"]     = df_final.groupby("id_station")["target_pct"].shift(1008)

        weather_map = {
            "ciel dégagé"           : 0,
            "peu nuageux"           : 1,
            "partiellement nuageux" : 2,
            "couvert"               : 3,
            "nuageux"               : 4,
            "averses"               : 5,
            "pluie"                 : 6,
            "orage"                 : 7,
            "neige"                 : 8,
            "brume"                 : 9
        }
        df_final["description_code"] = df_final["description"].map(weather_map).fillna(-1)

        # ============================
        # ✅ Prédiction vectorisée
        # ============================
        logger.info("Prédiction...")

        X     = df_final[FEATURES]
        preds = np.round(model.predict(X) * df_final["capacity"])

        df_final["prediction"] = preds

        # ============================
        # ✅ Construction sortie_prediction
        # ============================
        for _, row in df_final.iterrows():
            sortie_prediction.append({
                "id_station"         : row["id_station"],
                "heure"              : row["heure"],
                "date"               : row["date"],
                "prediction_nb_velo" : int(row["prediction"])
            })

        print(f"sortie_prediction  {sortie_prediction}")
        return sortie_prediction

    except Exception as e:
        logger.error(f"Erreur : {e}")
        raise





def prediction_metro(id_arret_transport, nom_arret_transport, heures, date):


    metros = PostgreRequest.extrat_info_proximiter(id_arret_transport, nom_arret_transport)
    sortie_prediction = []
    metro_filtre = metros["id_station"].drop_duplicates()
    print( f"metro_filtre  {metro_filtre}")


    if isinstance(metro_filtre, pd.DataFrame):

        metro_filtre = metro_filtre.iloc[:, 0]

    return  prediction_station(metro_filtre, heures, date) 




if __name__ == "__main__":

  
    heures = [  "23:00", "18:00" , "20:00"]
    #prediction_station( 11218807773 , heures , "2026-05-11")
    prediction_metro('' , "Cadet" , heures , "2026-05-11")

