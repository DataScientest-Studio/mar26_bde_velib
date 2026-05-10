import os
import sys
from datetime import datetime, timezone
import psycopg2
from sqlalchemy import create_engine
import pandas as pd



sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config.logger_config import setup_logger 
logger = setup_logger()
from dotenv import load_dotenv
load_dotenv()

pg_conn = psycopg2.connect(
            database="db_velib",
            user= os.getenv("PG_LOGIN"),
            password= os.getenv("PG_PASSWORD"),
            host= os.getenv("PG_HOST"),
            port= os.getenv("PG_PORT")
        )


class PostgreRequest:

    def dernnier_inserted_at(Base):

        """
        recuper le dernier heure du dernier message dans la table station_status_flat
        :

        sortie : date 
        
        """
        with pg_conn.cursor() as cur:
            cur.execute(f"SELECT inserted_at FROM {Base} ORDER BY inserted_at DESC LIMIT 1;")
            row = cur.fetchone()
            if row:
            
                return row[0] 
            return datetime(2000, 1, 1, tzinfo=timezone.utc)
        
    def insert_meteo( data):

        if not data: return
        with pg_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO meteo (city_name, temp, humidity, description, wind_speed, inserted_at) VALUES %s",
                [(d["city"], d["temp"], d["humidity"], d["desc"], d["wind"], d["date"]) for d in data]
            )
        pg_conn.commit()
        #print(f"☀️ {datetime.now(timezone.utc)} - {len(data)} météo insérée(s).")
        logger.info(f"☀️ - {len(data)} météo insérée(s).")



    
    def insert_stations_info( stations: list[dict]) -> None:

        """ 
        Insertion ou mise à jour des informations de référence des stations
        """
        if not stations:
            logger.warning(f"⚠️ - Aucune Information de station à insérer.")
            #print(f"⚠️    {datetime.now(timezone.utc)} - Aucune Information de station à insérer.")
            return
        
        with pg_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO station_info_flat (id_station , name , capacity ,  latitude, longitude)
                VALUES %s
                ON CONFLICT (id_station) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    capacity = EXCLUDED.capacity,
                    latitude = EXCLUDED.latitude,
                    longitude = EXCLUDED.longitude;
                """,
                [(s["station_id"], s["name"], s["capacity"] , s["lat"], s["lon"] )
                for s in stations]
            )
        pg_conn.commit()
        #print(f"✅    {datetime.now(timezone.utc)} - {len(stations)} information  stations insérées dans PostgreSQL.")
        logger.info(f"✅ - {len(stations)} information  stations insérées dans PostgreSQL.")



    def insert_stations_satut( stations: list[dict]) -> None:

        """ 
        Insertion des données de station_status dans la table
        """
        
        if not stations:
            logger.warning(f"⚠️ - Aucune Information de station à insérer.")
            #print(f"⚠️    {datetime.now(timezone.utc)} - Aucune statut station à insérer .")
            return

        with pg_conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                """
                INSERT INTO station_status_flat
                    (id_station, num_docks_available, num_bikes_mechanical, num_bikes_ebike, inserted_at)
                VALUES %s
                """,
                [(s["station_id"], s["docker_total"], s["mechanical"], s["ebike"] , s["date"])
                for s in stations]
            )
        pg_conn.commit()
        #print(f"✅    {datetime.now(timezone.utc)} -  {len(stations)} Statut stations insérées dans PostgreSQL.")
        logger.info(f"✅ - {len(stations)} Statut stations insérées dans PostgreSQL.")


    @staticmethod
    def extract_postgres_data_training():
        # Construction de l'URL de connexion (URI)
        user = os.getenv("PG_LOGIN")
        password = os.getenv("PG_PASSWORD")
        host = os.getenv("PG_HOST")
        port = os.getenv("PG_PORT")
        dbname = "db_velib"
        
        # Format : postgresql://user:password@host:port/dbname
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        
        try:
            # Création du moteur SQLAlchemy
            engine = create_engine(connection_string)

            query = """
               SELECT 
                    s.id_station, 
                    s.num_docks_available, 
                    s.num_bikes_mechanical, 
                    s.num_bikes_ebike,
                    (s.num_bikes_mechanical + s.num_bikes_ebike) as num_bikes_available,
                    i.capacity, 
                    s.inserted_at as collected_at,
                    w.temp, 
                    w.humidity, 
                    w.wind_speed,
                    w.description , 
                    w.inserted_at ,
                    w.city_name
                FROM station_status_flat s
                JOIN station_info_flat i ON s.id_station = i.id_station
                LEFT JOIN meteo w ON  DATE_TRUNC('hour', s.inserted_at) = DATE_TRUNC('hour', w.inserted_at) 
                WHERE  w.city_name  ='Paris'  
                
                ORDER BY RANDOM() LIMIT 25000000; """    #LIMIT 30000000 ;
            
            
            
            with engine.connect() as conn:
                df = pd.read_sql_query(query, conn)
            return df

        except Exception as e:
            print(f"Erreur lors de l'extraction : {e}")
            return None
        
    def extrat_postgres_data(id_station):


        try:



                
            query = f"""
                SELECT 
                    s.id_station, 
                    s.num_docks_available, 
                    s.num_bikes_mechanical, 
                    s.num_bikes_ebike,
                    (s.num_bikes_mechanical + s.num_bikes_ebike) as num_bikes_available,
                    i.capacity, 
                    s.inserted_at as collected_at,
                    w.temp, 
                    w.humidity, 
                    w.wind_speed,
                    w.description , 
                    w.inserted_at ,
                    w.city_name
                FROM station_status_flat s
                JOIN station_info_flat i ON s.id_station = i.id_station
                LEFT JOIN meteo w ON  DATE_TRUNC('hour', s.inserted_at) = DATE_TRUNC('hour', w.inserted_at) 
                
                WHERE  w.city_name  ='Paris' and  s.id_station in {id_station}
                and s.inserted_at = (SELECT inserted_at from station_status_flat ORDER BY inserted_at DESC LIMIT 1)
                

            """
            

            df = pd.read_sql_query(query, pg_conn)
            
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None


    def extrat_info_station(idstation) :

            try:


                query = f"""
                    SELECT * FROM station_info_flat 
                    where id_station = {idstation}
                    

                """
                

                df = pd.read_sql_query(query, pg_conn)
                
                return df

            except Exception as e:
                print(f"Erreur de connexion ou de requête : {e}")
                return None
            

            
    def extrat_info_proximiter(id_arret_transport=None, nom_arret_transport=None):
        try:
            if id_arret_transport is None and nom_arret_transport is None:
                print("Erreur : il faut au moins un paramètre")
                return None

            
            if id_arret_transport == '':
                id_arret_transport = None

            
            if id_arret_transport is not None and nom_arret_transport is not None:
                where = "arrname = %(nom)s OR transport_stops.id_transport_stop = %(id)s"
            elif id_arret_transport is not None:
                where = f"transport_stops.id_transport_stop = {id_arret_transport}"
            else:
                where = f"arrname = '{nom_arret_transport}'"

            query = f"""
                SELECT * FROM proximity 
                JOIN station_info_flat ON proximity.id_station = station_info_flat.id_station
                JOIN transport_stops ON proximity.id_transport_stop = transport_stops.id_transport_stop
                WHERE {where}
            """

            df = pd.read_sql_query(query, pg_conn)

            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None
