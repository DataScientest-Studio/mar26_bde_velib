import sys
import os
import pymongo
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
import psycopg2.extras
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.data.Postgre_Request import PostgreRequest
from src.data.Mongo_Request import MongoRequest
from src.config.logger_config import setup_logger 
logger = setup_logger( )

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")


def main() : 

    try:

        station = MongoRequest.extrate_mango_station_satut()
        PostgreRequest.insert_stations_satut(station)
        
        station = MongoRequest.extrate_mango_station_info()
        PostgreRequest.insert_stations_info(station)
        
        #station = mango_station_satut(pg_conn)
        #insert_stations(pg_conn, station)


        meteo = MongoRequest.extrate_mango_meteo()
        PostgreRequest.insert_meteo(meteo)


        
    except Exception as e:
       
        #print(f"⛔    {datetime.now(timezone.utc)} -  Erreur : {e}")
        logger.error(f"⛔ - Erreur : {e}")




if __name__ == "__main__":
    main()