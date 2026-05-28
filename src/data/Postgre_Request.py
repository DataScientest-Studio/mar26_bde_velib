import os
import sys
from datetime import datetime, timezone
import psycopg2
from sqlalchemy import create_engine
import pandas as pd

import os
from dotenv import load_dotenv
load_dotenv()
HOST = os.getenv("PG_HOST")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.config.logger_config import setup_logger 
logger = setup_logger()
from dotenv import load_dotenv
load_dotenv()

def get_pg_conn():
    return psycopg2.connect(
        database="db_velib",
        user=os.getenv("PG_LOGIN"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST"),
        port=os.getenv("PG_PORT")
    )

class PostgreRequest:

    def dernnier_inserted_at(Base):

        """
        Récupère l'horodatage du dernier enregistrement inséré dans une table 
        de la base de données PostgreSQL.

        Cette fonction interroge la table spécifiée pour retourner la valeur 
        maximale de la colonne inserted_at, permettant de déterminer la date 
        et l'heure de la dernière insertion effectuée.

        Parameters
        ----------
        Base : str
            Nom de la table PostgreSQL à interroger.
            La table doit obligatoirement contenir une colonne inserted_at 
            de type timestamp ou timestamptz.

            Exemples de valeurs attendues :
            - "station_status_flat"
            - "station_info_flat"
            - "meteo"

        Returns
        -------
        datetime
            Horodatage du dernier enregistrement inséré dans la table.

            - Si la table contient des enregistrements : retourne le datetime 
            correspondant à la valeur la plus récente de inserted_at.
            - Si la table est vide : retourne une date par défaut 
            datetime(2000, 1, 1, tzinfo=timezone.utc) afin de garantir 
            une valeur exploitable par l'appelant sans lever d'exception.

        Raises
        ------
        psycopg2.Error
            En cas d'erreur lors de l'exécution de la requête SQL PostgreSQL.
            Note : les exceptions ne sont pas interceptées dans cette fonction,
            elles se propagent à l'appelant.
        psycopg2.errors.UndefinedTable
            Si la table spécifiée dans Base n'existe pas dans la base de données.
        psycopg2.errors.UndefinedColumn
            Si la table spécifiée ne contient pas de colonne inserted_at.

        Notes
        -----
        - La requête SQL utilisée est :
            SELECT inserted_at FROM {Base} ORDER BY inserted_at DESC LIMIT 1
        - La valeur par défaut datetime(2000, 1, 1, tzinfo=timezone.utc) 
        est retournée lorsque la table est vide, afin d'éviter de retourner 
        None et de simplifier les comparaisons temporelles chez l'appelant.
        - Le paramètre Base est injecté directement dans la requête SQL 
        (f-string). Il est recommandé de s'assurer que la valeur provient 
        d'une source contrôlée pour éviter tout risque d'injection SQL.
        - La fonction repose sur une connexion PostgreSQL globale (pg_conn) 
        initialisée en dehors de la fonction.

        Examples
        --------
        >>> # Récupération du dernier statut de station inséré
        >>> last_update = dernnier_inserted_at("station_status_flat")
        >>> print(last_update)
        2024-01-15 08:30:00+00:00

        >>> # Récupération de la dernière météo insérée
        >>> last_meteo = dernnier_inserted_at("meteo")
        >>> print(last_meteo)
        2024-01-15 08:00:00+00:00

        >>> # Cas d'une table vide : retour de la date par défaut
        >>> last_update = dernnier_inserted_at("station_status_flat")
        >>> print(last_update)
        2000-01-01 00:00:00+00:00
        """
        

        conn = get_pg_conn()
        with conn.cursor() as cur:
            cur.execute(f"SELECT inserted_at FROM {Base} ORDER BY inserted_at DESC LIMIT 1;")
            row = cur.fetchone()
            if row:
            
                return row[0] 
            return datetime(2000, 1, 1, tzinfo=timezone.utc)
        
        
    def insert_meteo( data):
        """
        Insère les données météorologiques dans la table meteo 
        de la base de données PostgreSQL.

        Cette fonction réalise une insertion en lot (batch insert) des relevés 
        météorologiques via psycopg2.extras.execute_values pour optimiser 
        les performances lors d'insertions massives.

        Parameters
        ----------
        data : list[dict]
            Liste de dictionnaires contenant les données météorologiques 
            à insérer.

            Chaque dictionnaire doit contenir les clés suivantes :
            - "city"     (str)      : Nom de la ville (ex : "Paris")
            - "temp"     (float)    : Température en degrés Celsius
            - "humidity" (int)      : Taux d'humidité en pourcentage (0-100)
            - "desc"     (str)      : Description des conditions météo
                                    (ex : "ciel dégagé", "pluie légère")
            - "wind"     (float)    : Vitesse du vent en m/s
            - "date"     (datetime) : Horodatage du relevé météorologique

            Si la liste est vide ou None, la fonction retourne immédiatement 
            sans effectuer d'insertion.

        Returns
        -------
        None
            La fonction ne retourne aucune valeur.
            Les résultats sont directement persistés en base de données.

        Raises
        ------
        psycopg2.Error
            En cas d'erreur lors de l'insertion ou du commit PostgreSQL.
            Note : les exceptions ne sont pas interceptées dans cette fonction,
            elles se propagent à l'appelant.
        KeyError
            Si un dictionnaire de la liste ne contient pas toutes les clés 
            attendues ("city", "temp", "humidity", "desc", "wind", "date").

        Notes
        -----
        - Contrairement à insert_stations_info(), cette fonction utilise 
        un INSERT simple sans gestion des conflits (ON CONFLICT).
        Chaque appel insère de nouveaux enregistrements historiques.
        - La vérification de la liste vide est réalisée avec un return 
        immédiat (sans journalisation d'avertissement), contrairement 
        aux fonctions insert_stations_info() et insert_stations_satut().
        - Un commit explicite (conn.commit()) est effectué après l'insertion 
        pour valider la transaction.
        - La fonction repose sur une connexion PostgreSQL globale (pg_conn) 
        initialisée en dehors de la fonction.
        - Les insertions sont journalisées via logger.info() avec le nombre 
        de relevés insérés.

        Colonnes insérées dans meteo
        ----------------------------
        - city_name   : Nom de la ville
        - temp        : Température en degrés Celsius
        - humidity    : Taux d'humidité en pourcentage
        - description : Description des conditions météorologiques
        - wind_speed  : Vitesse du vent en m/s
        - inserted_at : Horodatage du relevé météorologique

        Comparaison des fonctions d'insertion
        --------------------------------------
        | Critère           | insert_meteo     | insert_stations_info | insert_stations_satut |
        |-------------------|------------------|----------------------|-----------------------|
        | Table cible       | meteo            | station_info_flat    | station_status_flat   |
        | Stratégie         | INSERT simple    | UPSERT               | INSERT simple         |
        | Gestion liste vide| return silencieux| logger.warning()     | logger.warning()      |
        | Historique        | ✅ conservé      | ❌ (écrasé)          | ✅ conservé           |

        Examples
        --------
        >>> # Insertion d'un relevé météorologique
        >>> data = [
        ...     {
        ...         "city"     : "Paris",
        ...         "temp"     : 18.5,
        ...         "humidity" : 72,
        ...         "desc"     : "ciel dégagé",
        ...         "wind"     : 3.2,
        ...         "date"     : datetime(2024, 1, 15, 8, 0, 0)
        ...     }
        ... ]
        >>> insert_meteo(data)
        >>> # Log attendu : ☀️ - 1 météo insérée(s).

        >>> # Cas d'une liste vide : retour immédiat sans journalisation
        >>> insert_meteo([])
        >>> # Aucun log, aucune insertion
        """

        if not data: return
        conn = get_pg_conn()
        with conn.cursor() as cur:
            psycopg2.extras.execute_values(
                cur,
                "INSERT INTO meteo (city_name, temp, humidity, description, wind_speed, inserted_at) VALUES %s",
                [(d["city"], d["temp"], d["humidity"], d["desc"], d["wind"], d["date"]) for d in data]
            )
        conn.commit()
        #print(f"☀️ {datetime.now(timezone.utc)} - {len(data)} météo insérée(s).")
        logger.info(f"☀️ - {len(data)} météo insérée(s).")



    
    def insert_stations_info( stations: list[dict]) -> None:

        """
        Insère ou met à jour les informations de référence des stations Vélib' 
        dans la table station_info_flat de la base de données PostgreSQL.

        Cette fonction réalise un UPSERT (INSERT ... ON CONFLICT DO UPDATE) 
        en lot via psycopg2.extras.execute_values. Si une station existe déjà 
        (conflit sur id_station), ses informations sont mises à jour avec 
        les nouvelles valeurs fournies.

        Parameters
        ----------
        stations : list[dict]
            Liste de dictionnaires contenant les informations de référence 
            de chaque station Vélib'.

            Chaque dictionnaire doit contenir les clés suivantes :
            - "station_id"  (int ou str) : Identifiant unique de la station
            - "name"        (str)        : Nom de la station
            - "capacity"    (int)        : Capacité totale de la station
                                        (nombre total de bornes)
            - "lat"         (float)      : Latitude GPS de la station
            - "lon"         (float)      : Longitude GPS de la station

            Si la liste est vide, la fonction journalise un avertissement 
            et retourne sans effectuer d'insertion.

        Returns
        -------
        None
            La fonction ne retourne aucune valeur.
            Les résultats sont directement persistés en base de données.

        Raises
        ------
        psycopg2.Error
            En cas d'erreur lors de l'insertion, du UPSERT ou du commit PostgreSQL.
            Note : les exceptions ne sont pas interceptées dans cette fonction,
            elles se propagent à l'appelant.
        KeyError
            Si un dictionnaire de la liste ne contient pas toutes les clés 
            attendues ("station_id", "name", "capacity", "lat", "lon").

        Notes
        -----
        - La stratégie UPSERT garantit l'idempotence de la fonction :
        elle peut être appelée plusieurs fois avec les mêmes données 
        sans créer de doublons.
        - En cas de conflit sur id_station, les champs suivants sont mis à jour :
            * name, capacity, latitude, longitude
        - La fonction utilise psycopg2.extras.execute_values pour réaliser 
        l'UPSERT en lot, plus performant que des insertions/mises à jour unitaires.
        - Un commit explicite (conn.commit()) est effectué après l'opération 
        pour valider la transaction.
        - La fonction repose sur une connexion PostgreSQL globale (pg_conn) 
        initialisée en dehors de la fonction.

        Différence avec insert_stations_satut()
        ----------------------------------------
        | Critère             | insert_stations_info     | insert_stations_satut       |
        |---------------------|--------------------------|-----------------------------|
        | Table cible         | station_info_flat        | station_status_flat         |
        | Type de données     | Référentiel (statique)   | Statut (temporel)           |
        | Stratégie           | UPSERT (ON CONFLICT)     | INSERT simple               |
        | Doublons possibles  | ❌ (clé unique gérée)    | ✅ (historique conservé)    |

        Colonnes insérées/mises à jour dans station_info_flat
        ------------------------------------------------------
        - id_station : Identifiant unique de la station (clé primaire)
        - name       : Nom de la station
        - capacity   : Capacité totale de la station
        - latitude   : Latitude GPS de la station
        - longitude  : Longitude GPS de la station

        Examples
        --------
        >>> # Insertion initiale de nouvelles stations
        >>> stations = [
        ...     {
        ...         "station_id" : 12345,
        ...         "name"       : "Rivoli - Hôtel de Ville",
        ...         "capacity"   : 30,
        ...         "lat"        : 48.8566,
        ...         "lon"        : 2.3522
        ...     },
        ...     {
        ...         "station_id" : 67890,
        ...         "name"       : "Bastille - Beaumarchais",
        ...         "capacity"   : 25,
        ...         "lat"        : 48.8533,
        ...         "lon"        : 2.3692
        ...     }
        ... ]
        >>> insert_stations_info(stations)
        >>> # Log attendu : ✅ - 2 information stations insérées dans PostgreSQL.

        >>> # Mise à jour d'une station existante (capacité modifiée)
        >>> stations_updated = [
        ...     {
        ...         "station_id" : 12345,
        ...         "name"       : "Rivoli - Hôtel de Ville",
        ...         "capacity"   : 35,
        ...         "lat"        : 48.8566,
        ...         "lon"        : 2.3522
        ...     }
        ... ]
        >>> insert_stations_info(stations_updated)
        >>> # Log attendu : ✅ - 1 information stations insérées dans PostgreSQL.

        >>> # Cas d'une liste vide : aucune insertion, avertissement journalisé
        >>> insert_stations_info([])
        >>> # Log attendu : ⚠️ - Aucune Information de station à insérer.
        """


        if not stations:
            logger.warning(f"⚠️ - Aucune Information de station à insérer.")
            #print(f"⚠️    {datetime.now(timezone.utc)} - Aucune Information de station à insérer.")
            return
        
        conn = get_pg_conn()
        with conn.cursor() as cur:
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
        conn.commit()
        #print(f"✅    {datetime.now(timezone.utc)} - {len(stations)} information  stations insérées dans PostgreSQL.")
        logger.info(f"✅ - {len(stations)} information  stations insérées dans PostgreSQL.")



    def insert_stations_satut( stations: list[dict]) -> None:

        """
        Insère les données de statut des stations Vélib' dans la table 
        station_status_flat de la base de données PostgreSQL.

        Cette fonction réalise une insertion en lot (batch insert) des statuts 
        de stations Vélib' en utilisant psycopg2.extras.execute_values pour 
        optimiser les performances lors d'insertions massives.

        Parameters
        ----------
        stations : list[dict]
            Liste de dictionnaires contenant les informations de statut 
            de chaque station Vélib'.
            
            Chaque dictionnaire doit contenir les clés suivantes :
            - "station_id"    (int ou str) : Identifiant unique de la station
            - "docker_total"  (int)        : Nombre de places libres disponibles
            - "mechanical"    (int)        : Nombre de vélos mécaniques disponibles
            - "ebike"         (int)        : Nombre de vélos électriques disponibles
            - "date"          (datetime)   : Horodatage de la collecte du statut

            Si la liste est vide, la fonction journalise un avertissement 
            et retourne sans effectuer d'insertion.

        Returns
        -------
        None
            La fonction ne retourne aucune valeur.
            Les résultats sont directement persistés en base de données.

        Raises
        ------
        psycopg2.Error
            En cas d'erreur lors de l'insertion ou du commit PostgreSQL.
            Note : les exceptions ne sont pas interceptées dans cette fonction,
            elles se propagent à l'appelant.
        KeyError
            Si un dictionnaire de la liste ne contient pas toutes les clés 
            attendues ("station_id", "docker_total", "mechanical", "ebike", "date").

        Notes
        -----
        - La fonction utilise psycopg2.extras.execute_values pour réaliser 
        une insertion en lot, plus performante que des insertions unitaires.
        - Un commit explicite (conn.commit()) est effectué après l'insertion 
        pour valider la transaction.
        - Si la liste stations est vide, un avertissement est journalisé 
        via logger.warning() et la fonction retourne immédiatement sans 
        accéder à la base de données.
        - Les résultats sont journalisés via logger.info() avec le nombre 
        de stations insérées.
        - La fonction repose sur une connexion PostgreSQL globale (pg_conn) 
        initialisée en dehors de la fonction.

        Colonnes insérées dans station_status_flat
        ------------------------------------------
        - id_station          : Identifiant unique de la station
        - num_docks_available : Nombre de places libres disponibles
        - num_bikes_mechanical: Nombre de vélos mécaniques disponibles
        - num_bikes_ebike     : Nombre de vélos électriques disponibles
        - inserted_at         : Horodatage de la collecte

        Examples
        --------
        >>> # Insertion d'un lot de statuts de stations
        >>> stations = [
        ...     {
        ...         "station_id"   : 12345,
        ...         "docker_total" : 10,
        ...         "mechanical"   : 5,
        ...         "ebike"        : 3,
        ...         "date"         : datetime(2024, 1, 15, 8, 30, 0)
        ...     },
        ...     {
        ...         "station_id"   : 67890,
        ...         "docker_total" : 2,
        ...         "mechanical"   : 8,
        ...         "ebike"        : 2,
        ...         "date"         : datetime(2024, 1, 15, 8, 30, 0)
        ...     }
        ... ]
        >>> insert_stations_satut(stations)
        >>> # Log attendu : ✅ - 2 Statut stations insérées dans PostgreSQL.

        >>> # Cas d'une liste vide : aucune insertion, avertissement journalisé
        >>> insert_stations_satut([])
        >>> # Log attendu : ⚠️ - Aucune Information de station à insérer.
        """
        
        
        if not stations:
            logger.warning(f"⚠️ - Aucune Information de station à insérer.")
            #print(f"⚠️    {datetime.now(timezone.utc)} - Aucune statut station à insérer .")
            return

        conn = get_pg_conn()
        with conn.cursor() as cur:
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
        conn.commit()
        #print(f"✅    {datetime.now(timezone.utc)} -  {len(stations)} Statut stations insérées dans PostgreSQL.")
        logger.info(f"✅ - {len(stations)} Statut stations insérées dans PostgreSQL.")


    @staticmethod
    def extract_postgres_data_training():
        """
        Extrait un large échantillon de données historiques des stations Vélib' 
        enrichies avec les conditions météorologiques, destiné à l'entraînement 
        de modèles de Machine Learning.

        Cette fonction se connecte à la base de données PostgreSQL via SQLAlchemy 
        et extrait jusqu'à 25 000 000 enregistrements historiques combinant 
        l'état des stations Vélib' et les données météorologiques de Paris, 
        dans un ordre aléatoire pour garantir la représentativité de l'échantillon.

        Parameters
        ----------
        Aucun paramètre requis.
        Les credentials de connexion sont récupérés automatiquement 
        depuis les variables d'environnement suivantes :
            - PG_LOGIN    : Nom d'utilisateur PostgreSQL
            - PG_PASSWORD : Mot de passe PostgreSQL
            - PG_HOST     : Hôte du serveur PostgreSQL
            - PG_PORT     : Port du serveur PostgreSQL
        La base de données cible est fixée à "db_velib".

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant jusqu'à 25 000 000 lignes avec les colonnes 
            suivantes :

            Informations sur la station :
            - id_station              (int)       : Identifiant unique de la station
            - capacity                (int)       : Capacité totale de la station

            État historique de la station :
            - num_docks_available     (int)       : Nombre de places libres disponibles
            - num_bikes_mechanical    (int)       : Nombre de vélos mécaniques disponibles
            - num_bikes_ebike         (int)       : Nombre de vélos électriques disponibles
            - num_bikes_available     (int)       : Nombre total de vélos disponibles
                                                    (num_bikes_mechanical + num_bikes_ebike)
            - collected_at            (timestamp) : Horodatage du snapshot collecté

            Données météorologiques (Paris) :
            - temp                    (float)     : Température en degrés Celsius
            - humidity                (int)       : Humidité relative en pourcentage (%)
            - wind_speed              (float)     : Vitesse du vent en m/s
            - description             (str)       : Description des conditions météo
                                                    (ex: "ciel dégagé", "pluie légère")
            - inserted_at             (timestamp) : Horodatage de la collecte météo
            - city_name               (str)       : Nom de la ville (toujours "Paris")

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.


        Sources des données
        -------------------
        Tables utilisées :
        - station_status_flat : État historique des stations Vélib'
                                (vélos disponibles, places libres, horodatage...)
        - station_info_flat   : Informations statiques des stations Vélib'
                                (capacité...)
        - meteo               : Données météorologiques horaires par ville
                                (température, humidité, vent, description...)

        Examples
        --------
        >>> # Extraction du jeu de données d'entraînement
        >>> df_training = extract_postgres_data_training()
        >>> if df_training is not None:
        ...     print(f"Nombre de lignes extraites : {len(df_training)}")
        ...     print(f"Colonnes disponibles       : {list(df_training.columns)}")
        ...     print(df_training.head())
        ... else:
        ...     print("Erreur lors de l'extraction des données d'entraînement")

        >>> # Vérification de la distribution des données
        >>> df_training = extract_postgres_data_training()
        >>> if df_training is not None:
        ...     print(df_training['num_docks_available'].describe())
        ...     print(df_training['temp'].describe())
        """


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
            
            
            conn = get_pg_conn()
            with engine.connect() as conn:
                df = pd.read_sql_query(query, conn)
            return df

        except Exception as e:
            print(f"Erreur lors de l'extraction : {e}")
            return None
        
    def extrat_postgres_data(id_station):
        """
        Extrait les données en temps réel d'une ou plusieurs stations Vélib' 
        enrichies avec les conditions météorologiques actuelles de Paris.

        Cette fonction interroge la base de données PostgreSQL pour récupérer 
        le dernier snapshot disponible des stations spécifiées, joint avec 
        les données météorologiques correspondantes à la même heure.

        Parameters
        ----------
        id_station : int ou str
            Identifiant(s) unique(s) de la ou des stations Vélib'.
            - Si int  : identifiant unique d'une station (ex: 12345)
            - Si str  : identifiant(s) sous forme de chaîne,
                        peut contenir plusieurs valeurs séparées par des virgules
                        (ex: "12345, 67890")
            - Paramètre obligatoire : aucune valeur par défaut,
            une valeur None provoquera une erreur SQL.

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant les colonnes suivantes :

            Informations sur la station :
            - id_station              (int)       : Identifiant unique de la station
            - capacity                (int)       : Capacité totale de la station

            État en temps réel (dernier snapshot) :
            - num_docks_available     (int)       : Nombre de places libres disponibles
            - num_bikes_mechanical    (int)       : Nombre de vélos mécaniques disponibles
            - num_bikes_ebike         (int)       : Nombre de vélos électriques disponibles
            - num_bikes_available     (int)       : Nombre total de vélos disponibles
                                                    (num_bikes_mechanical + num_bikes_ebike)
            - collected_at            (timestamp) : Horodatage du dernier snapshot collecté

            Données météorologiques (Paris) :
            - temp                    (float)     : Température en degrés Celsius
            - humidity                (int)       : Humidité relative en pourcentage (%)
            - wind_speed              (float)     : Vitesse du vent en m/s
            - description             (str)       : Description textuelle des conditions météo
                                                    (ex: "ciel dégagé", "pluie légère")
            - inserted_at             (timestamp) : Horodatage de la collecte météo
            - city_name               (str)       : Nom de la ville (toujours "Paris")

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.

        Notes
        -----
        - Seul le dernier snapshot disponible est retourné (INSERT le plus récent 
        dans station_status_flat).
        - La jointure avec la table météo est effectuée sur l'heure tronquée 
        (DATE_TRUNC('hour')) pour faire correspondre les données à la même heure.
        - Les données météorologiques sont filtrées sur la ville de Paris uniquement.
        - La jointure avec la météo est de type LEFT JOIN mais le filtre 
        WHERE w.city_name = 'Paris' transforme implicitement ce LEFT JOIN 
        en INNER JOIN : si aucune donnée météo n'est disponible pour l'heure 
        correspondante, aucune ligne ne sera retournée.
        - Le paramètre id_station est injecté directement dans le f-string SQL,
        ce qui expose la fonction à des risques d'injection SQL.

        Sources des données
        -------------------
        Tables utilisées :
        - station_status_flat : État en temps réel des stations Vélib'
                                (vélos disponibles, places libres, horodatage...)
        - station_info_flat   : Informations statiques des stations Vélib'
                                (capacité...)
        - meteo               : Données météorologiques horaires par ville
                                (température, humidité, vent, description...)

        Examples
        --------
        >>> # Extraction pour une station unique
        >>> df = extrat_postgres_data(id_station=12345)
        >>> print(df)

        >>> # Extraction pour plusieurs stations
        >>> df = extrat_postgres_data(id_station="12345, 67890")
        >>> print(df)

        >>> # Affichage des conditions météo et de la disponibilité
        >>> df = extrat_postgres_data(id_station=12345)
        >>> if df is not None and not df.empty:
        ...     row = df.iloc[0]
        ...     print(f"Station         : {row['id_station']}")
        ...     print(f"Places libres   : {row['num_docks_available']}")
        ...     print(f"Vélos dispo     : {row['num_bikes_available']}")
        ...     print(f"Température     : {row['temp']}°C")
        ...     print(f"Météo           : {row['description']}")
        ...     print(f"Vent            : {row['wind_speed']} m/s")
        ... else:
        ...     print("Aucune donnée disponible")
        """
        try:

            query = f""" SELECT  s.id_station, 
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
                
                WHERE  w.city_name  ='Paris' and  s.id_station in ({id_station})
                and s.inserted_at = (SELECT inserted_at from station_status_flat ORDER BY inserted_at DESC LIMIT 1)
            """
            

            df = pd.read_sql_query(query, get_pg_conn())
            
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None
        
    def extrat_postgres_data_pre(id_station):
        """
        Extrait les données en temps réel d'une ou plusieurs stations Vélib' 
        avec les valeurs historiques de référence (lag 24h et lag 7 jours).

        Cette fonction interroge la base de données PostgreSQL pour récupérer 
        le dernier snapshot disponible des stations spécifiées, enrichi avec 
        les valeurs de disponibilité observées 24 heures et 7 jours auparavant, 
        afin de permettre une analyse comparative temporelle.

        Parameters
        ----------
        id_station : int, str ou list
            Identifiant(s) unique(s) de la ou des stations Vélib'.
            - Si int  : identifiant unique d'une station (ex: 12345)
            - Si str  : identifiant(s) sous forme de chaîne,
                        peut contenir plusieurs valeurs séparées par des virgules
                        (ex: "12345, 67890")
            - Paramètre obligatoire : aucune valeur par défaut, 
            une valeur None provoquera une erreur SQL.

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant les colonnes suivantes :

            Informations sur la station :
            - id_station              (int)       : Identifiant unique de la station
            - capacity                (int)       : Capacité totale de la station

            État en temps réel (dernier snapshot) :
            - num_docks_available     (int)       : Nombre de places libres disponibles
            - num_bikes_mechanical    (int)       : Nombre de vélos mécaniques disponibles
            - num_bikes_ebike         (int)       : Nombre de vélos électriques disponibles
            - num_bikes_available     (int)       : Nombre total de vélos disponibles
                                                    (num_bikes_mechanical + num_bikes_ebike)
            - collected_at            (timestamp) : Horodatage du dernier snapshot collecté

            Données historiques de référence :
            - lag_24h                 (int)       : Nombre de places libres observées 
                                                    il y a 24 heures (snapshot le plus proche
                                                    antérieur à collected_at - 24h)
            - lag_7j                  (int)       : Nombre de places libres observées 
                                                    il y a 7 jours (snapshot le plus proche
                                                    antérieur à collected_at - 7 jours)

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.

        Notes
        -----
        - Seul le dernier snapshot disponible est retourné (INSERT le plus récent 
        dans station_status_flat).
        - Les valeurs lag_24h et lag_7j peuvent être NULL si aucun snapshot 
        n'est disponible pour la période de référence correspondante.
        - Les lags sont calculés via des sous-requêtes corrélées et portent 
        uniquement sur num_docks_available.
        - Le paramètre id_station est injecté directement dans le f-string SQL,
        ce qui expose la fonction à des risques d'injection SQL.

        Sources des données
        -------------------
        Tables utilisées :
        - station_status_flat : État en temps réel des stations Vélib'
                                (vélos disponibles, places libres, horodatage...)
        - station_info_flat   : Informations statiques des stations Vélib'
                                (capacité...)

        Examples
        --------
        >>> # Extraction pour une station unique
        >>> df = extrat_postgres_data_pre(id_station=12345)
        >>> print(df)

        >>> # Extraction pour plusieurs stations
        >>> df = extrat_postgres_data_pre(id_station="12345, 67890")
        >>> print(df)

        >>> # Analyse comparative avec les données historiques
        >>> df = extrat_postgres_data_pre(id_station=12345)
        >>> if df is not None:
        ...     row = df.iloc[0]
        ...     print(f"Station         : {row['id_station']}")
        ...     print(f"Places libres   : {row['num_docks_available']}")
        ...     print(f"Lag 24h         : {row['lag_24h']}")
        ...     print(f"Lag 7 jours     : {row['lag_7j']}")
        ...     variation_24h = row['num_docks_available'] - row['lag_24h']
        ...     print(f"Variation 24h   : {variation_24h:+d} places")
        ... else:
        ...     print("Erreur lors de la récupération des données")
        """

        try:


            query = f""" SELECT  s.id_station, 
                    s.num_docks_available, 
                    s.num_bikes_mechanical, 
                    s.num_bikes_ebike,
                    (s.num_bikes_mechanical + s.num_bikes_ebike) as num_bikes_available,
                    i.capacity, 
                    s.inserted_at as collected_at ,
                     (  SELECT s24.num_docks_available 
                      		FROM station_status_flat s24
                      		WHERE s24.id_station = s.id_station
                        	AND s24.inserted_at <= s.inserted_at - INTERVAL '24 hours'
                      		ORDER BY s24.inserted_at DESC
                      		LIMIT 1
                  	) AS lag_24h ,
                    
                    
                       (
                          SELECT s7.num_docks_available 
                          FROM station_status_flat s7
                          WHERE s7.id_station = s.id_station
                            AND s7.inserted_at <= s.inserted_at - INTERVAL '7 days'
                          ORDER BY s7.inserted_at DESC
                          LIMIT 1
                      ) AS lag_7j
    
    
    
                FROM station_status_flat s
                JOIN station_info_flat i ON s.id_station = i.id_station
              
                
                WHERE  /*w.city_name  ='Paris' and */ s.id_station in ({id_station})
                and s.inserted_at = (SELECT inserted_at from station_status_flat ORDER BY inserted_at DESC LIMIT 1)
                ORDER BY  s.inserted_at
                

            """
            
            df = pd.read_sql_query(query, get_pg_conn())
            
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None


    def extrat_info_station(id_station=None) :
            
        """
        Extrait les informations statiques d'une ou plusieurs stations Vélib' 
        à partir de leurs identifiants.

        Cette fonction interroge la base de données PostgreSQL pour récupérer 
        les informations détaillées des stations Vélib' correspondant aux 
        identifiants fournis.

        Parameters
        ----------
        id_station : int, str ou list, optional
            Identifiant(s) unique(s) de la ou des stations Vélib'.
            - Si int       : identifiant unique d'une station (ex: 12345)
            - Si str       : identifiant(s) sous forme de chaîne, 
                            peut contenir plusieurs valeurs séparées par des virgules
                            (ex: "12345, 67890")
            - Si list      : liste d'identifiants (ex: [12345, 67890])
            - Si None      : risque d'erreur SQL, aucune validation n'est effectuée.

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant toutes les colonnes de la table station_info_flat :
            - id_station  (int)   : Identifiant unique de la station
            - name        (str)   : Nom de la station Vélib'
            - latitude    (float) : Latitude géographique de la station
            - longitude   (float) : Longitude géographique de la station
            - capacity    (int)   : Capacité totale de la station 
                                    (nombre total d'emplacements)

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.

        Warnings
        --------
        - Aucune validation du paramètre id_station n'est effectuée avant 
        l'exécution de la requête SQL.
        - Si id_station est None, la requête SQL générée sera invalide 
        (WHERE id_station IN (None)) et provoquera une erreur.
        - Ce paramètre est directement injecté dans la requête SQL via un 
        f-string, ce qui expose la fonction à des risques d'injection SQL.
        Il est recommandé d'utiliser des paramètres liés (bind parameters) 
        pour sécuriser la requête.

        Sources des données
        -------------------
        Tables utilisées :
        - station_info_flat : Informations statiques des stations Vélib'
                            (nom, coordonnées GPS, capacité...)

        Examples
        --------
            >>> # Recherche par identifiant unique (int)
            >>> df = extrat_info_station(id_station=12345)
            >>> print(df)

            >>> # Recherche de plusieurs stations (str séparés par des virgules)
            >>> df = extrat_info_station(id_station="12345, 67890, 11111")
            >>> print(df)

            >>> # Vérification du résultat
            >>> df = extrat_info_station(id_station=12345)
            >>> if df is not None:
            ...     print(f"Station trouvée : {df['name'].iloc[0]}")
            ...     print(f"Capacité        : {df['capacity'].iloc[0]} vélos")
            ... else:
            ...     print("Erreur lors de la récupération des données")
        """

        try:

            query = f""" SELECT * FROM station_info_flat 
                    where id_station in   ({id_station})
 
                """
                

            df = pd.read_sql_query(query, get_pg_conn())
                
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None
            

            
    def extrat_info_proximiter(id_arret_transport=None, nom_arret_transport=None):
        """
        Extrait les informations des stations Vélib' à proximité d'un arrêt 
        de transport en commun, recherché par son identifiant et/ou son nom.

        Cette fonction interroge la base de données PostgreSQL pour retrouver 
        toutes les stations Vélib' proches d'un arrêt de transport en commun 
        spécifié. La recherche peut se faire par identifiant, par nom, ou par 
        les deux simultanément.

        Parameters
        ----------
        id_arret_transport : int ou str, optional
            Identifiant unique de l'arrêt de transport en commun.
            - Si None ou '' (chaîne vide) : ce paramètre est ignoré.
            - Si renseigné : filtre sur l'identifiant de l'arrêt.

        nom_arret_transport : str, optional
            Nom de l'arrêt de transport en commun.
            - Si None : ce paramètre est ignoré.
            - Si renseigné : filtre sur le nom de l'arrêt (arrname).

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant toutes les colonnes des tables jointes :

            Depuis la table proximity :
            - id_station          (int)   : Identifiant de la station Vélib'
            - id_transport_stop   (int)   : Identifiant de l'arrêt de transport
            - distance            (float) : Distance en mètres entre la station 
                                            et l'arrêt de transport

            Depuis la table station_info_flat :
            - name                (str)   : Nom de la station Vélib'
            - latitude            (float) : Latitude géographique de la station
            - longitude           (float) : Longitude géographique de la station
            - capacity            (int)   : Capacité totale de la station

            Depuis la table transport_stops :
            - arrname             (str)   : Nom de l'arrêt de transport en commun
            - (autres colonnes disponibles dans transport_stops)

            Retourne None si aucun paramètre n'est fourni ou en cas d'erreur.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.

        Notes
        -----
        Comportement selon les paramètres fournis :

        +---------------------------+---------------------------+----------------------------------+
        | id_arret_transport        | nom_arret_transport       | Comportement                     |
        +---------------------------+---------------------------+----------------------------------+
        | None ou ''                | None                      | Erreur : retourne None           |
        | Renseigné                 | None                      | Filtre sur l'identifiant (AND)   |
        | None ou ''                | Renseigné                 | Filtre sur le nom (AND)          |
        | Renseigné                 | Renseigné                 | Filtre sur les deux (OR)         |
        +---------------------------+---------------------------+----------------------------------+

        - Lorsque les deux paramètres sont fournis, la condition est un OR :
        les résultats incluent les arrêts correspondant à l'un OU l'autre critère.
        - Une chaîne vide ('') pour id_arret_transport est traitée comme None.
        - Les jointures sont de type INNER JOIN : seules les stations ayant 
        des arrêts de transport référencés seront retournées.

        Sources des données
        -------------------
        Tables utilisées :
        - proximity           : Table de liaison entre stations Vélib' 
                                et arrêts de transport (contient la distance)
        - station_info_flat   : Informations statiques des stations Vélib'
        - transport_stops     : Informations sur les arrêts de transport en commun

        Examples
        --------
            >>> # Recherche par identifiant d'arrêt uniquement
            >>> df = extrat_info_proximiter(id_arret_transport=42)
            >>> print(df)

            >>> # Recherche par nom d'arrêt uniquement
            >>> df = extrat_info_proximiter(nom_arret_transport="Châtelet")
            >>> print(df)

            >>> # Recherche combinée (OR) : retourne les résultats pour l'un ou l'autre
            >>> df = extrat_info_proximiter(id_arret_transport=42, nom_arret_transport="Châtelet")
            >>> print(df)

            >>> # Cas d'erreur : aucun paramètre fourni
            >>> df = extrat_info_proximiter()
            >>> # Output : Erreur : il faut au moins un paramètre
            >>> print(df)  # None

            >>> # Cas particulier : chaîne vide traitée comme None
            >>> df = extrat_info_proximiter(id_arret_transport='', nom_arret_transport="Nation")
            >>> print(df)  # Recherche uniquement sur le nom "Nation"
        """
            


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

            df = pd.read_sql_query(query, get_pg_conn())

            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None


    def extrat_info_station_api(id_station=None ) :
        """
        Extrait les informations géographiques des stations Vélib' 
        ainsi que les arrêts de transport en commun à proximité.

        Cette fonction interroge la base de données PostgreSQL pour récupérer 
        les informations statiques des stations de vélos, enrichies avec 
        les données des arrêts de transport en commun proches.

        Parameters
        ----------
        id_station : int, optional
            Identifiant unique de la station Vélib'.
            - Si None (par défaut) : retourne les informations de toutes les stations.
            - Si renseigné : retourne uniquement les informations de la station spécifiée.

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant les colonnes suivantes :

            Informations sur la station :
            - id_station  (int)   : Identifiant unique de la station
            - name        (str)   : Nom de la station Vélib'
            - latitude    (float) : Latitude géographique de la station
            - longitude   (float) : Longitude géographique de la station

            Informations sur les transports à proximité :
            - arrname     (str)   : Nom de l'arrêt de transport en commun proche
            - distance    (float) : Distance en mètres entre la station 
                                    et l'arrêt de transport

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

        Raises
        ------
        Exception
            Les exceptions sont interceptées et affichées dans la console.
            La fonction retourne None en cas d'erreur.

        Notes
        -----
        - Les résultats sont triés par id_station (ORDER BY id_station).
        - Une station peut apparaître plusieurs fois dans le résultat si elle 
        est proche de plusieurs arrêts de transport en commun.
        - La table proximity fait le lien entre les stations Vélib' et 
        les arrêts de transport en commun.
        - Les deux jointures sont de type INNER JOIN, ce qui signifie que 
        seules les stations ayant au moins un arrêt de transport à proximité 
        seront retournées.

        Sources des données
        -------------------
        Tables utilisées :
        - proximity           : Table de liaison entre les stations Vélib' 
                                et les arrêts de transport (contient la distance)
        - station_info_flat   : Informations statiques des stations Vélib'
                                (nom, coordonnées GPS...)
        - transport_stops     : Informations sur les arrêts de transport 
                                en commun (nom de l'arrêt...)

        Examples
        --------
            >>> # Récupérer les informations de toutes les stations
            >>> df_toutes_stations = extrat_info_station_api()
            >>> print(df_toutes_stations.head())

            >>> # Récupérer les informations d'une station spécifique
            >>> df_station = extrat_info_station_api(id_station=12345)
            >>> print(df_station)

            >>> # Afficher les arrêts de transport proches d'une station
            >>> df_station = extrat_info_station_api(id_station=12345)
            >>> if df_station is not None:
            ...     print(f"Arrêts à proximité de la station {df_station['name'].iloc[0]} :")
            ...     for _, row in df_station.iterrows():
            ...         print(f"  - {row['arrname']} : {row['distance']:.0f} mètres")
            ... else:
            ...     print("Erreur lors de la récupération des données")
        """

        try:
            condition = ""

            if id_station == None :
                condition = ""
            else : 
                condition = f"where  station_info_flat.id_station  = {id_station}"


            query = f"""
                    SELECT 
                    station_info_flat.id_station , station_info_flat.name , station_info_flat.latitude , station_info_flat.longitude , 
                    transport_stops.arrname ,distance , station_info_flat.capacity

                    FROM proximity 
                    JOIN station_info_flat ON proximity.id_station = station_info_flat.id_station
                    JOIN transport_stops ON proximity.id_transport_stop = transport_stops.id_transport_stop
                        
                    {condition}       
                    ORDER BY station_info_flat.id_station
                        

                """



            df = pd.read_sql_query(query, get_pg_conn())
                    
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None
                

    def extrat_info_etat_api(id_station=None ) :

        """
        Extrait les informations en temps réel sur l'état des stations Vélib' 
        combinées avec les données météorologiques.

        Cette fonction interroge la base de données PostgreSQL pour récupérer 
        les dernières données disponibles concernant l'état des stations de vélos, 
        enrichies avec les informations météorologiques de Paris.

        Parameters
        ----------
        id_station : int, optional
            Identifiant unique de la station Vélib'.
            - Si None (par défaut) : retourne les données de toutes les stations.
            - Si renseigné : retourne uniquement les données de la station spécifiée.

        Returns
        -------
        pandas.DataFrame
            Un DataFrame contenant les colonnes suivantes :

                Informations sur les vélos :
                - id_station         (int)      : Identifiant unique de la station
                - nb_velo            (int)      : Nombre total de vélos disponibles
                                                (mécaniques + électriques)
                - nb_velo_classique  (int)      : Nombre de vélos mécaniques disponibles
                - nb_velo_electrique (int)      : Nombre de vélos électriques disponibles
                - nb_place_libre     (int)      : Nombre d'emplacements libres
                - capacite_totale    (int)      : Capacité totale de la station
                - derniere_maj       (datetime) : Date et heure de la dernière mise à jour

                Informations météorologiques :
                - description        (str)      : Description des conditions météo
                                                (ex: "ciel dégagé", "nuageux")
                - temperature        (float)    : Température en degrés Celsius
                - humidite           (float)    : Taux d'humidité en pourcentage
                - vent               (float)    : Vitesse du vent en m/s

            Retourne None en cas d'erreur de connexion ou d'exécution de la requête.

            Raises
            ------
            Exception
                Les exceptions sont interceptées et affichées dans la console.
                La fonction retourne None en cas d'erreur.

            Notes
            -----
            - Les données retournées correspondent uniquement au dernier snapshot 
            disponible dans la table station_status_flat.
            - La jointure avec la table météo est effectuée sur l'heure tronquée 
            (DATE_TRUNC('hour')) pour faire correspondre les données.
            - Les données météorologiques sont filtrées sur la ville de Paris.
            - La jointure avec station_info_flat est de type INNER JOIN (obligatoire).
            - La jointure avec la table météo est de type LEFT JOIN (optionnelle).

            Sources des données
            -------------------
            Tables utilisées :
            - station_status_flat  : État en temps réel des stations (vélos disponibles,
                                    places libres...)
            - station_info_flat    : Informations statiques des stations (capacité...)
            - meteo                : Données météorologiques horodatées

            Examples
            --------
                >>> # Récupérer l'état de toutes les stations
                >>> df_toutes_stations = extrat_info_etat_api()
                >>> print(df_toutes_stations.head())

                >>> # Récupérer l'état d'une station spécifique
                >>> df_station = extrat_info_etat_api(id_station=12345)
                >>> print(df_station)

                >>> # Vérifier si la requête a abouti
                >>> if df_station is not None:
                ...     print(f"Nombre de résultats : {len(df_station)}")
                ... else:
                ...     print("Erreur lors de la récupération des données")
        """

        try:
            condition = ""

            if id_station == None :
                condition1 = ""
                condition2 = ""
            else : 
                condition1 = f"WHERE id_station = {id_station}"
                condition2 = f"WHERE s.id_station = {id_station}"

            query = f"""
                    WITH last_update AS (
                        SELECT MAX(inserted_at) as inserted_at
                        FROM station_status_flat
                        {condition1}
                    ),
                    target_hour AS (
                        SELECT DATE_TRUNC('hour', inserted_at) as hour_trunc
                        FROM last_update
                    )
                    SELECT 
                        s.id_station, 
                        (s.num_bikes_mechanical + s.num_bikes_ebike)  AS nb_velo,
                        s.num_bikes_mechanical                         AS nb_velo_classique,
                        s.num_bikes_ebike                              AS nb_velo_electrique,
                        s.num_docks_available                          AS nb_place_libre,
                        i.capacity                                     AS capacite_totale, 
                        s.inserted_at                                  AS derniere_maj,
                        w.description, 
                        w.temp                                         AS temperature, 
                        w.humidity                                     AS humidite, 
                        w.wind_speed                                   AS vent 
                    FROM station_status_flat s
                    JOIN last_update lu      ON s.inserted_at = lu.inserted_at
                    JOIN station_info_flat i ON s.id_station = i.id_station
                    LEFT JOIN meteo w        ON w.inserted_at >= (SELECT hour_trunc FROM target_hour)
                                            AND w.inserted_at  < (SELECT hour_trunc FROM target_hour) + INTERVAL '1 hour'
                                            AND w.city_name = 'Paris'
                    {condition2};    
                    """

            df = pd.read_sql_query(query, get_pg_conn())
                    
            return df

        except Exception as e:
            print(f"Erreur de connexion ou de requête : {e}")
            return None
                


