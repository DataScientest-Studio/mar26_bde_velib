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

FEATURES = [
            "id_station", "hour_sin", "hour_cos",
            "min_sin", "min_cos", "day_of_week",
            "temp", "humidity", "wind_speed",
            "description_code", "capacity" ,


            "lag_24h", "lag_7j"
        ]


class Presiction :

    def __init__(self, model_path: Path = Path("models/model.pkl")):

        self.model_path = model_path
        self.model = joblib.load(self.model_path)
        self.meteo_key = os.getenv("METEO_KEY")


    #METEO_KEY= os.getenv("METEO_KEY")




    def appel_prediction(self, station , h , m) :

        """
        Réalise une prédiction du nombre de vélos disponibles pour une station 
        Vélib' donnée à partir d'un modèle de Machine Learning pré-entraîné.

        Cette fonction orchestre l'ensemble du pipeline de prédiction :
        récupération des données en temps réel depuis PostgreSQL, feature 
        engineering (encodage cyclique du temps, variables météo, lags 
        temporels), inférence du modèle et conversion du résultat en nombre 
        de vélos disponibles.

        Parameters
        ----------
        model : sklearn estimator (ou compatible)
            Modèle de Machine Learning pré-entraîné et chargé en mémoire 
            (ex : chargé via joblib.load()).
            Doit exposer une méthode predict(X) retournant des valeurs 
            comprises entre 0 et 1 (taux de disponibilité en pourcentage).

        station : int ou str
            Identifiant unique de la station Vélib' pour laquelle effectuer 
            la prédiction. Transmis directement à extrat_postgres_data().

        h : int
            Heure cible pour la prédiction (0-23).
            Utilisée pour calculer les features d'encodage cyclique 
            hour_sin et hour_cos indépendamment de l'heure réelle 
            du snapshot PostgreSQL.

        m : int
            Minute cible pour la prédiction (0-59).
            Utilisée pour calculer les features d'encodage cyclique 
            min_sin et min_cos.

        Returns
        -------
        numpy.ndarray ou None
            Tableau NumPy contenant les prédictions arrondies du nombre 
            de vélos disponibles pour chaque ligne du dataset récupéré.

            - En cas de succès : array de valeurs entières (np.round appliqué)
            représentant le nombre de vélos disponibles prédit.
            - En cas d'erreur (dataset vide, colonne manquante, erreur SQL...) :
            retourne None et journalise l'erreur via logger.error().

        Raises
        ------
        Aucune exception n'est propagée à l'appelant.
        Toutes les exceptions sont interceptées par le bloc try/except 
        et journalisées via logger.error().

        Notes
        -----
        Features utilisées pour la prédiction (FEATURES)
        -------------------------------------------------
        Les colonnes sélectionnées pour le modèle sont définies par la 
        constante globale FEATURES. Elles incluent notamment :
            - hour_sin, hour_cos   : Encodage cyclique de l'heure (période 24h)
            - min_sin, min_cos     : Encodage cyclique des minutes (période 60min)
            - day_of_week          : Jour de la semaine (0=lundi, 6=dimanche)
            - lag_24h              : Taux de disponibilité observé 24h avant 
                                    (shift de 144 pas de 10 minutes)
            - lag_7j               : Taux de disponibilité observé 7 jours avant 
                                    (shift de 1008 pas de 10 minutes)
            - description_code     : Conditions météo encodées numériquement
            - temp, humidity, wind_speed : Variables météorologiques continues

        Encodage des conditions météorologiques (weather_map)
        ------------------------------------------------------
        | Description             | Code |
        |-------------------------|------|
        | ciel dégagé             |  0   |
        | peu nuageux             |  1   |
        | partiellement nuageux   |  2   |
        | couvert                 |  3   |
        | nuageux                 |  4   |
        | averses                 |  5   |
        | pluie                   |  6   |
        | orage                   |  7   |
        | neige                   |  8   |
        | brume                   |  9   |
        | (inconnu)               | -1   |

        Pipeline de prédiction
        ----------------------
        1. Récupération des données temps réel via extrat_postgres_data()
        2. Extraction des composantes temporelles (hour, day_of_week)
        3. Calcul des encodages cycliques (hour_sin/cos, min_sin/cos)
        4. Calcul du taux de disponibilité cible (target_pct)
        5. Calcul des lags temporels (lag_24h, lag_7j)
        6. Encodage des conditions météorologiques (description_code)
        7. Sélection des features (FEATURES) et inférence du modèle
        8. Conversion du taux prédit en nombre de vélos (× capacity)

        Examples
        --------
        >>> # Prédiction pour la station 12345 à 8h30
        >>> preds = appel_prediction(model, station=12345, h=8, m=30)
        >>> if preds is not None:
        ...     print(f"Vélos prédits : {int(preds[0])}")
        Vélos prédits : 12

        >>> # Prédiction en heure de pointe (18h00)
        >>> preds = appel_prediction(model, station=67890, h=18, m=0)
        >>> if preds is not None:
        ...     print(f"Vélos prédits : {int(preds[0])}")
        Vélos prédits : 3

        >>> # Cas d'erreur (station inexistante ou dataset vide)
        >>> preds = appel_prediction(model, station=99999, h=8, m=0)
        >>> print(preds)
        None
        """

        
        try :

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
            preds =  np.round( self.model.predict(X) * df['capacity'] )

            df["prediction"] = preds

            return preds
        except Exception as e:
            logger.error( f" Ereeur : {e} ")

    def prediction_meteo( self, longetude , latitude  , heures , date ) :

        """
        Récupère les prévisions météorologiques pour une position géographique 
        donnée et une liste d'horaires cibles via l'API OpenWeatherMap Forecast.

        Cette fonction interroge l'endpoint /forecast de l'API OpenWeatherMap 
        (prévisions toutes les 3 heures sur 5 jours) et filtre les résultats 
        pour ne retourner que les créneaux correspondant aux horaires demandés, 
        avec une fenêtre de tolérance de 3 heures autour de chaque heure cible.

        Parameters
        ----------
        longetude : float
            Longitude du point géographique pour lequel récupérer les prévisions.
            Valeurs attendues : entre -180 et 180.
            Exemple : 2.3488 (Paris)

        latitude : float
            Latitude du point géographique pour lequel récupérer les prévisions.
            Valeurs attendues : entre -90 et 90.
            Exemple : 48.8534 (Paris)

        heures : list of str
            Liste des heures cibles pour lesquelles filtrer les prévisions.
            Format attendu pour chaque élément : "HH:MM" (ex: "08:00", "18:30").
            Pour chaque heure, la fonction recherche une prévision OpenWeatherMap 
            dans la fenêtre [heure_cible ; heure_cible + 2h59min].

        date : str
            Date cible pour les prévisions météorologiques.
            Format attendu : "YYYY-MM-DD" (ex: "2024-01-15").
            Doit être comprise dans les 5 prochains jours (limite API Forecast).

        Returns
        -------
        list of dict
            Liste de dictionnaires contenant les prévisions météo filtrées.
            Chaque dictionnaire correspond à un créneau horaire trouvé et 
            contient les clés suivantes :

            - date        (str)   : Date de la prévision (format "YYYY-MM-DD")
            - heure       (str)   : Heure cible demandée (format "HH:MM")
            - temp        (float) : Température en degrés Celsius
            - humidity    (int)   : Humidité relative en pourcentage (0-100)
            - wind_speed  (float) : Vitesse du vent en m/s
            - description (str)   : Description textuelle des conditions météo 
                                    en français (ex: "ciel dégagé", "pluie légère")

            Retourne une liste vide [] si aucune prévision ne correspond 
            aux critères de date et d'heure demandés.

        Notes
        -----
        API OpenWeatherMap
        ------------------
        - Endpoint   : https://api.openweathermap.org/data/2.5/forecast
        - Clé API    : Chargée depuis la constante METEO_KEY (variable 
                    d'environnement ou fichier de configuration)
        - Fréquence  : Prévisions toutes les 3 heures
        - Horizon    : 5 jours glissants à partir de maintenant
        - Unités     : metric (température en °C, vent en m/s)
        - Langue     : fr (descriptions météo en français)
        - Timeout    : 10 secondes

        Fenêtre de correspondance temporelle
        -------------------------------------
        Pour chaque heure demandée, la fonction recherche une prévision 
        dont le timestamp dt_txt est compris dans la fenêtre :

            [date + heure_cible  ;  date + heure_cible + 2h59min]

        Ce pas de 3 heures correspond à la granularité de l'API Forecast.
        Une même prévision OpenWeatherMap peut ainsi correspondre à 
        plusieurs heures demandées si elles sont proches.

        Compatibilité avec insert_meteo()
        ----------------------------------
        Les dictionnaires retournés sont compatibles avec la fonction 
        insert_meteo(), qui attend les clés :
        "city", "temp", "humidity", "desc", "wind", "date".
        Une adaptation des clés est nécessaire avant insertion.

        Examples
        --------
        >>> # Prévisions pour Paris à 8h et 18h le 15 janvier 2024
        >>> resultats = prediction_meteo(
        ...     longetude = 2.3488,
        ...     latitude  = 48.8534,
        ...     heures    = ["08:00", "18:00"],
        ...     date      = "2024-01-15"
        ... )
        >>> for r in resultats:
        ...     print(f"{r['heure']} - {r['temp']}°C - {r['description']}")
        08:00 - 5.2°C - ciel dégagé
        18:00 - 3.8°C - peu nuageux

        >>> # Résultat pour une seule heure
        >>> resultats = prediction_meteo(2.3488, 48.8534, ["12:00"], "2024-01-15")
        >>> print(resultats[0])
        {
            'date'       : '2024-01-15',
            'heure'      : '12:00',
            'temp'       : 7.4,
            'humidity'   : 72,
            'wind_speed' : 3.2,
            'description': 'nuageux'
        }

        >>> # Aucun résultat si la date est hors des 5 prochains jours
        >>> resultats = prediction_meteo(2.3488, 48.8534, ["08:00"], "2030-01-01")
        >>> print(resultats)
        []
        """


        url = f'https://api.openweathermap.org/data/2.5/forecast?appid={self.meteo_key}&units=metric&lang=fr&lat={latitude}&lon={longetude}'
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


                if date_demande <= date_prediction <= date_fin:

                    resultats.append({         
                        'date': date , 
                        'heure' : heure,             
                        'temp': prediction['main']['temp'], 
                        'humidity': prediction['main']['humidity'],   
                        'wind_speed': prediction['wind']['speed'],      
                        'description': prediction['weather'][0]['description']
                    })

        return resultats


    def prediction_station(self,idstation, heures, date):

        """
        Prédit le nombre de vélos disponibles pour une ou plusieurs stations 
        Vélib' à des horaires et une date donnés.

        Cette fonction orchestre l'ensemble du pipeline de prédiction batch :
        récupération des informations stations, des données temps réel PostgreSQL, 
        des prévisions météorologiques OpenWeatherMap, fusion des sources de données, 
        feature engineering et inférence vectorisée du modèle Random Forest.

        Parameters
        ----------
        idstation : int ou list of int
            Identifiant(s) de la ou des stations Vélib' pour lesquelles 
            réaliser les prédictions.
            Si un entier est fourni, il est automatiquement converti en liste.
            Exemple : 12345 ou [12345, 67890, 11111]

        heures : list of str
            Liste des heures cibles pour lesquelles prédire la disponibilité.
            Format attendu pour chaque élément : "HH:MM".
            Exemple : ["08:00", "12:00", "18:00"]

        date : str
            Date cible pour les prédictions.
            Format attendu : "YYYY-MM-DD".
            Doit être comprise dans les 5 prochains jours (limite API Forecast).
            Exemple : "2024-01-15"

        Returns
        -------
        list of dict
            Liste de dictionnaires, un par combinaison (station × heure), 
            contenant les clés suivantes :

            - id_station         (int) : Identifiant de la station Vélib'
            - heure              (str) : Heure de la prédiction (format "HH:MM")
            - date               (str) : Date de la prédiction (format "YYYY-MM-DD")
            - prediction_nb_velo (int) : Nombre de vélos prédit disponibles

        Raises
        ------
        ValueError
            Si le DataFrame final est vide après les fusions ou si les 
            features attendues par le modèle sont absentes.

        Exception
            Toute erreur survenant lors du feature engineering ou de 
            l'inférence du modèle est loguée via logger.error() et 
            re-levée pour traitement par l'appelant.

        Notes
        -----
        Pipeline d'exécution
        --------------------
        1. Normalisation de idstation en liste
        2. Récupération des infos stations via extrat_info_station()
        (coordonnées GPS, capacité, nom)
        3. Récupération des données temps réel via extrat_postgres_data_pre()
        (num_bikes_available, num_docks_available, collected_at)
        4. Récupération des prévisions météo via prediction_meteo()
        (1 requête API par station, coordonnées GPS individuelles)
        5. Fusion 1  : df_station ⟕ df_postgres  (clé : id_station, outer join)
        6. Fusion 2  : df_fusion_1 ⟕ df_meteo    (clé : id_station, inner join)
        7. Feature engineering :
        - Extraction hour, day_of_week depuis collected_at
        - Encodage cyclique hour_sin/cos, min_sin/cos depuis l'heure météo
        - Calcul target_pct = num_bikes_available / capacity
        - Encodage description météo → description_code (weather_map)
        8. Inférence vectorisée : model.predict(X[FEATURES]) × capacity
        9. Construction et retour de sortie_prediction

        Encodage météo (weather_map)
        ----------------------------
        | Description             | Code |
        |-------------------------|------|
        | ciel dégagé             |  0   |
        | peu nuageux             |  1   |
        | partiellement nuageux   |  2   |
        | couvert                 |  3   |
        | nuageux                 |  4   |
        | averses                 |  5   |
        | pluie                   |  6   |
        | orage                   |  7   |
        | neige                   |  8   |
        | brume                   |  9   |
        | (inconnu)               | -1   |

        Gestion des erreurs de fusion
        -----------------------------
        Si un merge échoue (colonnes manquantes ou types incompatibles), 
        la fonction bascule automatiquement sur un cross join pour 
        garantir la continuité du pipeline.

        Dépendances globales
        --------------------
        - model   : RandomForestRegressor pré-chargé (joblib)
        - FEATURES : liste des features attendues par le modèle
        - logger  : logger Python configuré en amont

        Examples
        --------
        >>> # Prédiction pour une station, deux horaires
        >>> resultats = prediction_station(
        ...     idstation = 12345,
        ...     heures    = ["08:00", "18:00"],
        ...     date      = "2024-01-15"
        ... )
        >>> for r in resultats:
        ...     print(f"Station {r['id_station']} à {r['heure']} : {r['prediction_nb_velo']} vélos")
        Station 12345 à 08:00 : 14 vélos
        Station 12345 à 18:00 : 3 vélos

        >>> # Prédiction batch pour plusieurs stations
        >>> resultats = prediction_station(
        ...     idstation = [12345, 67890],
        ...     heures    = ["12:00"],
        ...     date      = "2024-01-15"
        ... )
        >>> print(len(resultats))  # 2 stations × 1 heure = 2 résultats
        2
        >>> print(resultats[0])
        {
            'id_station'         : 12345,
            'heure'              : '12:00',
            'date'               : '2024-01-15',
            'prediction_nb_velo' : 9
        }

        """

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
            meteo = self.prediction_meteo(
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
            preds = np.round(self.model.predict(X) * df_final["capacity"])

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



    def prediction_metro(self,id_arret_transport, nom_arret_transport, heures, date):

        """
        Prédit le nombre de vélos disponibles dans les stations Vélib' situées 
        à proximité d'un arrêt de transport en commun (métro, RER, bus, etc.).

        Cette fonction constitue une surcouche de prediction_station() : elle 
        résout d'abord les stations Vélib' proches d'un arrêt de transport via 
        la base PostgreSQL, puis délègue l'ensemble du pipeline de prédiction 
        à prediction_station().

        Parameters
        ----------
        id_arret_transport : int ou str
            Identifiant unique de l'arrêt de transport en commun dans la base 
            de données de proximité.
            Exemple : 1234 (identifiant RATP ou IDFM)

        nom_arret_transport : str
            Nom de l'arrêt de transport en commun.
            Utilisé conjointement avec id_arret_transport pour filtrer 
            les stations Vélib' proches dans la table de proximité.
            Exemple : "Châtelet", "Nation", "Gare de Lyon"

        heures : list of str
            Liste des heures cibles pour lesquelles prédire la disponibilité.
            Format attendu pour chaque élément : "HH:MM".
            Exemple : ["08:00", "12:00", "18:00"]

        date : str
            Date cible pour les prédictions.
            Format attendu : "YYYY-MM-DD".
            Doit être comprise dans les 5 prochains jours (limite API Forecast).
            Exemple : "2024-01-15"

        Returns
        -------
        list of dict
            Liste de dictionnaires retournée par prediction_station(), 
            un par combinaison (station Vélib' proche × heure), 
            contenant les clés suivantes :

            - id_station         (int) : Identifiant de la station Vélib'
            - heure              (str) : Heure de la prédiction (format "HH:MM")
            - date               (str) : Date de la prédiction (format "YYYY-MM-DD")
            - prediction_nb_velo (int) : Nombre de vélos prédit disponibles

            Retourne une liste vide [] si aucune station Vélib' n'est 
            référencée à proximité de l'arrêt demandé.

        Notes
        -----
        Pipeline d'exécution
        --------------------
        1. Récupération des stations Vélib' proches via extrat_info_proximiter()
        (filtre sur id_arret_transport + nom_arret_transport)
        2. Déduplication des id_station retournés
        3. Normalisation en Series si le résultat est un DataFrame
        4. Délégation à prediction_station() avec la liste des stations proches

        Table de proximité
        ------------------
        La fonction s'appuie sur la table PostgreSQL de proximité entre 
        arrêts de transport et stations Vélib', peuplée en amont lors 
        de l'ingestion des données géographiques.
        Colonnes attendues en retour de extrat_info_proximiter() :
        - id_station : identifiant de la station Vélib' proche
        - (autres colonnes de proximité ignorées ici)

        Relation avec prediction_station()
        ------------------------------------
        Cette fonction est un point d'entrée métier orienté "transport" :
        l'utilisateur raisonne en termes d'arrêt de métro/bus, et la fonction 
        résout automatiquement les stations Vélib' associées avant de 
        lancer la prédiction.

        Examples
        --------
        >>> # Vélos disponibles près de la station "Nation" à 8h et 18h
        >>> resultats = prediction_metro(
        ...     id_arret_transport    = 1234,
        ...     nom_arret_transport   = "Nation",
        ...     heures                = ["08:00", "18:00"],
        ...     date                  = "2024-01-15"
        ... )
        >>> for r in resultats:
        ...     print(f"Station {r['id_station']} à {r['heure']} : {r['prediction_nb_velo']} vélos")
        Station 11042 à 08:00 : 7 vélos
        Station 11042 à 18:00 : 2 vélos
        Station 11043 à 08:00 : 12 vélos
        Station 11043 à 18:00 : 5 vélos

        >>> # Aucune station Vélib' à proximité
        >>> resultats = prediction_metro(9999, "Arrêt Inconnu", ["08:00"], "2024-01-15")
        >>> print(resultats)

        """


        metros = PostgreRequest.extrat_info_proximiter(id_arret_transport, nom_arret_transport)
        sortie_prediction = []
        metro_filtre = metros["id_station"].drop_duplicates()
        print( f"metro_filtre  {metro_filtre}")


        if isinstance(metro_filtre, pd.DataFrame):

            metro_filtre = metro_filtre.iloc[:, 0]

        return  self.prediction_station(metro_filtre, heures, date) 




"""
if __name__ == "__main__":

  
    heures = [  "23:00", "18:00" , "20:00"]
    pre = Presiction()
    pre.prediction_station( 11218807773 , heures , "2026-05-11")
    #prediction_metro('' , "Cadet" , heures , "2026-05-11")

"""