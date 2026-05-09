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
                print(prediction['dt_txt'])
                print(prediction['main']['temp'])
                print(prediction['weather'][0]['description'])

                resultats.append({         
                    'date': date , 
                    'heure' : heure,             
                    'temp': prediction['main']['temp'],         
                    'description': prediction['weather'][0]['description']
                })

    return resultats

        


def prediction_station( idstation , heures , date ) :

    station = PostgreRequest.extrat_info_station(idstation)
    meteos = prediction_meteo(station["longitude"][0] , station["latitude"][0] , heures , date  )

    print(f"{station}  latitude =  {station["latitude"][0]}"  )
    print(f"meteo  {meteos}")


    try :

        logger.info("Chargement données...")
        df = PostgreRequest.extrat_postgres_data(idstation)

        sortie_prediction = []

        print(f"   colonnes = {list(df.columns)}")

        if df.empty:
            raise ValueError("Dataset vide")

        for meteo in meteos :

            logger.info("Feature engineering...")

            df["collected_at"] = pd.to_datetime(df["collected_at"])

            df["hour"] = df["collected_at"].dt.hour

            h = int(meteo['heure'].split(':')[0])
            m = int(meteo['heure'].split(':')[1])
            print( f" h {h} m {m}")
            
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
            sortie_prediction.append ( {
                'id_station' : idstation ,
                'heure' :meteo['heure']  ,
                'date' : meteo['date'] ,
                'prediction_nb_velo' : int(preds[0])

            })
            df["prediction"] = preds

        print( f"sortie_prediction  {sortie_prediction}")
        return sortie_prediction
    except Exception as e:
        logger.error( f" Ereeur : {e} ")


if __name__ == "__main__":

    table = []
    """

    model = joblib.load(MODEL_PATH)

    

    for h in range(21,24):
        for m in range(0, 60, 15):
            
            test = appel_prediction(model , 11218807773, h, m)
            table.append({"hour": f"{h}:{m}", "prediction": test})
            print(f"{h}:{m} - {test}")

    df = pd.DataFrame(table)
    df.head()

    """
    heures = [  "18:00", "19:00" , "20:00"]
    prediction_station( 11218807773 , heures , "2026-05-10")

