
import pymongo
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URL = os.getenv("MONGO_URL")



def message(pg_conn):

    """
    recuper le dernier heure du dernier message dans la table station_status_flat
    :

    sortie : date 
    
    """
    with pg_conn.cursor() as cur:
        cur.execute("SELECT inserted_at FROM station_status_flat ORDER BY inserted_at DESC LIMIT 1;")
        row = cur.fetchone()
        if row:
         
            return row[0] 
        return datetime(2000, 1, 1, tzinfo=timezone.utc)



def mango_station_satut( pg_conn): 


    """
    Extration des donnée depuis la base de données MongoDB .
    
    
    """
    myclient = pymongo.MongoClient(MONGO_URL)
    try :
        mydb = myclient["db_velib"]
        mycol = mydb["station_status"]


        date = message(pg_conn)
        print(f"Dernier enregistrement :  {date}")
        stations_filtre = mycol.find({"_ingested_at": {"$gt": date }})
        
        table_stations = []

        for stations in stations_filtre :
            
            extracted_at = stations['_ingested_at']
            print(f" date : {extracted_at}")


        
            stations = stations['data']['stations']
            #table_stations = []
            print('test')
            for station in  stations :
                
                

                velo_total  = station.get('num_bikes_available')
                
                docker_total = station.get('num_docks_available')
                station_id = station['station_id']
                #print(f" Station Id { station_id}  ")

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


                    #"extracted_at": extracted_at,

                })

                
                #return extracted_at , table_stations
        return table_stations
            
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        myclient.close()


def mango_station_info( pg_conn): 


    """
    Extration des donnée depuis la base de données MongoDB .
    
    
    """
    myclient = pymongo.MongoClient(MONGO_URL)
    try :
        mydb = myclient["db_velib"]
        mycol = mydb["station_info"]


        date = message(pg_conn)
        print(f"Dernier enregistrement :   {date}")
        stations_filtre = mycol.find({"_ingested_at": {"$gt": date }})
        
        table_stations = []

        for stations in stations_filtre :
            
            extracted_at = stations['_ingested_at']
            print(f" date {extracted_at}")


        
            stations = stations['data']['stations']
            #table_stations = []
            for station in  stations :
                


                station_id = station['station_id']
                name = station['name']
                capacity = station['capacity']
                lat = station['lat']
                lon = station['lon']
  
                table_stations.append({
                    "station_id": station_id,
                    "name" : name ,
                    "capacity" : capacity ,
                    "lat" : lat ,
                    "lon" : lon
                })
    
            
        return table_stations
    except Exception as e:
        print(f"Erreur : {e}")
    finally:
        myclient.close()


def create_table(pg_conn) -> None:

    """
    Creation de la table station_status_flat dans PostgreSQL
    
    """
    with pg_conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS station_status_flat (
                id                  SERIAL PRIMARY KEY,
                station_id          BIGINT NOT NULL,
                num_docks_available INT,
                num_bikes_mechanical INT,
                num_bikes_ebike     INT,
                inserted_at         TIMESTAMPTZ DEFAULT NOW()
            );
                    
            ALTER TABLE station_info_flat ALTER COLUMN station_id TYPE BIGINT;
            ALTER TABLE station_status_flat ALTER COLUMN station_id TYPE BIGINT;
                    

            CREATE TABLE IF NOT EXISTS station_info_flat ( 
                station_id    BIGINT PRIMARY KEY, 
                name          TEXT NOT NULL,
                capacity      INT NOT NULL,    
                lat           DOUBLE PRECISION NOT NULL,
                lon           DOUBLE PRECISION NOT NULL) ;
        """)
    pg_conn.commit()



def insert_stations(pg_conn, stations: list[dict]) -> None:

    """ 
    Insertion des données de station_status dans la table
    """
    if not stations:
        print("Aucune station à insérer.")
        return

    with pg_conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO station_status_flat
                (station_id, num_docks_available, num_bikes_mechanical, num_bikes_ebike, inserted_at)
            VALUES %s
            """,
            [(s["station_id"], s["docker_total"], s["mechanical"], s["ebike"] , s["date"])
             for s in stations]
        )
    pg_conn.commit()
    print(f"{len(stations)} Statut stations insérées dans PostgreSQL.")
  


def insert_stations_info(pg_conn, stations: list[dict]) -> None:

    """ 
    Insertion ou mise à jour des informations de référence des stations
    """
    if not stations:
        print("Aucune station à insérer.")
        return

    with pg_conn.cursor() as cur:
        psycopg2.extras.execute_values(
            cur,
            """
            INSERT INTO station_info_flat (station_id , name , capacity ,  lat, lon)
            VALUES %s
            ON CONFLICT (station_id) 
            DO UPDATE SET 
                name = EXCLUDED.name,
                capacity = EXCLUDED.capacity,
                lat = EXCLUDED.lat,
                lon = EXCLUDED.lon;
            """,
            [(s["station_id"], s["name"], s["capacity"] , s["lat"], s["lon"] )
             for s in stations]
        )
    pg_conn.commit()
    print(f"{len(stations)} information  stations insérées dans PostgreSQL.")


    

def main() : 


    
    pg_conn = psycopg2.connect(
            database="db_velib",
            user= os.getenv("PG_LOGIN"),
            password= os.getenv("PG_PASSWORD"),
            host= os.getenv("PG_HOST"),
            port= os.getenv("PG_PORT")
        )
    
    print(os.getenv("PG_PORT") )
    try:
        create_table(pg_conn) 

        
        station =  mango_station_info(pg_conn)
        insert_stations_info(pg_conn, station)

        
        station = mango_station_satut(pg_conn)
        insert_stations(pg_conn, station)
        
    except Exception as e:
        pg_conn.rollback()
        print(f"Erreur : {e}")
    finally:

        pg_conn.close()



   




main()
