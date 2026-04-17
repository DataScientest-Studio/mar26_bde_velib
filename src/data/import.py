import os
import requests
import pymongo
from datetime import datetime
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

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
    result = col.insert_one(data)
    #result = col.insert_many(data)
    print(f"Inserted: {result.inserted_id}")

def main(base , API_URL , headers_dict = None  ):
    client = pymongo.MongoClient(MONGO_URL)  
    

    
    try:
        data = appel_url(API_URL, headers_dict)
        data["_ingested_at"] = datetime.now(timezone.utc)
        
        insert_mongo(client, data, base )

    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main( "station_status" ,"https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json" )
    main( "station_info" ,"https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json" )

    #main( "medeo" ,f"https://api.openweathermap.org/data/2.5/weather?lat=48.8566&lon=2.3522&appid={os.getenv("METEO_KEY")}" )

    main( "medeo" ,f"https://api.openweathermap.org/data/2.5/weather?units=metric&lang=fr&q=paris&appid={os.getenv("METEO_KEY")}" )

    headers_dict ={
        "apikey": os.getenv("RER_KEY") ,

    }
    #main( "RER" ,"https://prim.iledefrance-mobilites.fr/marketplace//estimated-timetable?LineRef=ALL" , headers_dict )
    
