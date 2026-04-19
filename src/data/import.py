import os
import requests
import pymongo
from datetime import datetime
from datetime import datetime, timezone
import sys
import os
from dotenv import load_dotenv

import transform

#API_URL = "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json"

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")

#MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password1234@localhost:27017/")

def appel_url(url: str , headers_dict = None ) -> dict:
    
    headers = headers_dict if headers_dict else {}

    response = requests.get(url, headers=headers,  timeout=10)
    response.raise_for_status()  
    return response.json()



def insert_mongo(client: pymongo.MongoClient, data: dict, table_name: str) -> None:
    col = client["db_velib"][table_name]

    ecords = data.get("Siri", {}).get("ServiceDelivery", {}).get("EstimatedTimetableDelivery", [])

    deliveries = data.get("Siri", {}).get("ServiceDelivery", {}).get("EstimatedTimetableDelivery", [])
    
    if table_name == "rer_passage" and deliveries:
        all_records = []
        
        for d in deliveries:

            frames = d.get("EstimatedJourneyVersionFrame", [])
            for frame in frames:
                journeys = frame.get("EstimatedVehicleJourney", [])
                if isinstance(journeys, list):
                    all_records.extend(journeys)
                elif isinstance(journeys, dict):
                    all_records.append(journeys)
            
            direct_journeys = d.get("EstimatedVehicleJourney", [])
            if direct_journeys:
                if isinstance(direct_journeys, list):
                    all_records.extend(direct_journeys)
                else:
                    all_records.append(direct_journeys)

        if all_records:
            # On ajoute un timestamp pour savoir quand on a reçu l'info
            for r in all_records:
                r["_ingested_at"] = datetime.now(timezone.utc)
            
            result = col.insert_many(all_records)
            print(f"✅    {datetime.now(timezone.utc)} -  {table_name} : {len(result.inserted_ids)} records insérés.")
        else:
            print(f"⚠️    {datetime.now(timezone.utc)} - {table_name} : Reçu mais aucun trajet (Journey) trouvé dedans.")

    
    else :
        result = col.insert_one(data)
        #result = col.insert_many(data)
        #print(f"✅ Inserted {table_name}  : {result.inserted_id}")
        print(f"✅    {datetime.now(timezone.utc)} - Inserted {table_name}  : {result.inserted_id}")

def main(base , API_URL , headers_dict = None  ):
    client = pymongo.MongoClient(MONGO_URL)  
    

    
    try:
        data = appel_url(API_URL, headers_dict)
        data["_ingested_at"] = datetime.now(timezone.utc)
        
        insert_mongo(client, data, base )

    except Exception as e:
        print(f"⛔    {datetime.now(timezone.utc)} -  Erreur : {e}")
    finally:
        client.close()


        

if __name__ == "__main__":

    mode = sys.argv[1] if len(sys.argv) > 1 else "minute"

    if mode == "minute":
        print(f"🚲    {datetime.now(timezone.utc)} - Appel API  station_status ")
        main( "station_status" ,"https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json" )

        print(f"🚈 ℹ️ {datetime.now(timezone.utc)} - Appel API  info_trafic ")
        headers_dict ={ "apikey": os.getenv("RER_KEY") , }
        main( "info_trafic" ,"https://prim.iledefrance-mobilites.fr/marketplace/disruptions_bulk/disruptions/v2" , headers_dict )

    elif mode == "daily":    
        print(f"🚲 ℹ️ {datetime.now(timezone.utc)} - Appel API  station_info ")
        main( "station_info" ,"https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json" )

    #main( "medeo" ,f"https://api.openweathermap.org/data/2.5/weather?lat=48.8566&lon=2.3522&appid={os.getenv("METEO_KEY")}" )
    elif mode == "hourly":
        print(f"☀️    {datetime.now(timezone.utc)} - Appel API  medeo ")
        main( "medeo" ,f"https://api.openweathermap.org/data/2.5/weather?units=metric&lang=fr&q=paris&appid={os.getenv("METEO_KEY")}" )

    elif mode == "5minutes":
        print(f"🚈    {datetime.now(timezone.utc)} - Appel API  rer_passage ")
        headers_dict ={"apikey": os.getenv("RER_KEY") , }
        main( "rer_passage" ,"https://prim.iledefrance-mobilites.fr/marketplace//estimated-timetable?LineRef=ALL" , headers_dict )
    



    if mode == "minute":
        print(f"📞    {datetime.now(timezone.utc)} - Appel de la fonction transformation Mongo vers posgres") 
        transform.main()
        print(f"⏰    {datetime.now(timezone.utc)} - Fin de l'appel a la fonction tranformation") 
