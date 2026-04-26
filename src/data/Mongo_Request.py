import os
import sys
import requests
import pymongo
from pymongo import DESCENDING
from datetime import datetime, timezone



from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.config.logger_config import setup_logger 
logger = setup_logger()



MONGO_URL = os.getenv("MONGO_URL")
BDD= os.getenv("BDD")
client = pymongo.MongoClient(MONGO_URL)
db = client[str(BDD)]


class MongoRequest:

    
    def insert_mongo(data: dict, table_name: str) -> None:
        

        col = db[table_name]

        # "ecords" était une variable inutilisée, on peut la supprimer
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
                for r in all_records:
                    r["_ingested_at"] = datetime.now(timezone.utc)
                
                result = col.insert_many(all_records)
                logger.info(f"✅ - {table_name} : {len(result.inserted_ids)} records insérés.")
                #print(f"✅    {datetime.now(timezone.utc)} -  {table_name} : {len(result.inserted_ids)} records insérés.")
            else:
                logger.warning(f"⚠️ - {table_name} : Reçu mais aucun trajet (Journey) trouvé dedans.")
                #print(f"⚠️    {datetime.now(timezone.utc)} - {table_name} : Reçu mais aucun trajet (Journey) trouvé dedans.")

        else:
            # Pour les autres tables (comme velib), on insère le document brut
            result = col.insert_one(data)
            logger.info(f"✅ - Inserted {table_name}  : {result.inserted_id}")
            #print(f"✅    {datetime.now(timezone.utc)} - Inserted {table_name}  : {result.inserted_id}")


    def extrate_mango_meteo():
        """ Extrait les données météo de Mongo """

        #client = pymongo.MongoClient(MONGO_URL)
        try:
            
            col = db["medeo"]
            date = PostgreRequest.dernnier_inserted_at("meteo")
            
            cursor = col.find({"_ingested_at": {"$gt": date}})
            data = []
            #print( cursor  )
            for doc in cursor:
                print( doc  )
                data.append({
                    "city": doc.get("name"),
                    "temp": doc.get("main", {}).get("temp"),
                    "humidity": doc.get("main", {}).get("humidity"),
                    "desc": doc.get("weather", [{}])[0].get("description"),
                    "wind": doc.get("wind", {}).get("speed"),
                    "date": doc.get("_ingested_at")
                })
            return data
        except Exception as e:
            logger.error(f"⛔ - Erreur critique : {e}")
            return []
            #print(f"⛔ Erreur critique : {e}")
        #finally:
            #client.close()


    def extrate_mango_station_info():
        try:
            col = db["station_info"]

            # On récupère le dernier doc
            last_doc = col.find_one({}, sort=[("_ingested_at", DESCENDING)])
            
            if not last_doc:
            
                print("⚠️ Aucun document trouvé dans MongoDB.")
                return []

            # --- UTILISE .get() POUR ÉVITER LES ERREURS ---
            # .get('clef', valeur_par_défaut) ne plante jamais
            extracted_at = last_doc.get('_ingested_at', datetime.now(timezone.utc))
            
            # On descend dans l'arborescence prudemment
            data_content = last_doc.get('data', {})
            stations_list = data_content.get('stations', [])

            table_stations = []
            for station in stations_list:
                table_stations.append({
                    "station_id": station.get('station_id'),
                    "name": station.get('name'),
                    "capacity": station.get('capacity'),
                    "lat": station.get('lat'),
                    "lon": station.get('lon'),
                    "extracted_at": extracted_at # On utilise la date du doc parent
                })
            
            #print(f"✅ {len(table_stations)} stations prêtes pour Postgres.")
            logger.info(f"✅ - stations prêtes pour Postgres.")
            return table_stations

        except Exception as e:
            logger.error(f"⛔ - Erreur critique : {e}")
            return []


    def extrate_mango_station_satut( ): 

        
        """
        Extration des donnée depuis la base de données MongoDB .
        
        
        """
        #myclient = pymongo.MongoClient(MONGO_URL)
        try :
            #mydb = myclient["db_velib"]
            col = db["station_status"]


            date = PostgreRequest.dernnier_inserted_at("station_status_flat")
            #print(f"✅    {datetime.now(timezone.utc)} -Dernier enregistrement postgres:  {date}")
            logger.info(f"✅ - Dernier enregistrement postgres:  {date}")
            stations_filtre = col.find({"_ingested_at": {"$gt": date }})
            
            table_stations = []

            for doc in stations_filtre :
                
                extracted_at = doc['_ingested_at']
                #print(f"✅    {datetime.now(timezone.utc)} -Alimentation enregistrement dans mango : {extracted_at} ")
                logger.info(f"✅ - Alimentation enregistrement dans mango : {extracted_at} ")


            
                stations = doc['data']['stations']
                #table_stations = []
                
                for station in  stations :

                    velo_total  = station.get('num_bikes_available')
                    
                    docker_total = station.get('num_docks_available')
                    station_id = station['station_id']
                

                    mechanical = 0
                    ebike = 0

                    for disponible in  station.get("num_bikes_available_types"  , [])  :

                        mechanical += disponible.get("mechanical" , 0) 
                        ebike += disponible.get("ebike" ,0)

    

                    table_stations.append({
                        "station_id": station_id,
                        "docker_total" : docker_total ,
                        "mechanical" : mechanical ,
                        #"velo_total": velo_total,
                        "ebike" : ebike, 
                        "date" : extracted_at


                    })


            return table_stations
                
        except Exception as e:
            logger.error(f"⛔ - Erreur critique : {e}")
            return []

