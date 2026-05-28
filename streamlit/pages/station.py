import streamlit as st
import requests
import pandas as pd
from numpy.random import default_rng as rng
from streamlit_apexjs import st_apexcharts
import datetime


import os
from dotenv import load_dotenv
load_dotenv()
HOST = os.getenv("API_HOST")


url = f"http://{HOST}:8000/auth/login"

data = {
    "username": "alice",
    "password": "wonderland"
}

response = requests.post(url, data=data)
data = response.json()
df = pd.DataFrame([data])
print(df["access_token"][0])
access_token = df["access_token"][0]



# ── Récupérer l'id depuis session_state ────────────
id_station = st.session_state.get("id_station")


if not id_station:
    st.error(" Aucune station sélectionnée")
    st.stop()

st.title(f" Station #{id_station}")

# ── Appel API ──────────────────────────────────────
try:
    response = requests.get(f"http://{HOST}:8000/v1/stations/{id_station}", headers={"Authorization": f"Bearer {access_token}"} )
    etat = requests.get(f"http://{HOST}:8000/v1/stations/{id_station}/etat", headers={"Authorization": f"Bearer {access_token}"} )
    semaine_response = requests.get(f"http://{HOST}:8000/v1/statistiques/station/{id_station}/semaine", headers={"Authorization": f"Bearer {access_token}"} )

    if response.status_code == 200:
        station = response.json()
        semaine = semaine_response.json()


        st.subheader(station.get("nom_station", "Nom inconnu"))
        st.write("📍 Latitude :", station.get("latitude"))
        st.write("📍 Longitude :", station.get("longitude"))

        # Ajouter d'autres infos selon votre API
        #st.json(station)  
        

    

    if etat.status_code == 200:
        data = etat.json()
        st.subheader(" dispognibiliter")

        options = {
            "chart": {
                "toolbar": {
                    "show": False
                }
            },
            "labels": ["Vélos classiques", "Vélos électriques" , "Places libres"],
            "legend": {
                "show": True,
                "position": "bottom",
            },
            "colors": ["#316DDD", "#45D628" ,"#D62828"],
        }

        series = [
            data.get("nb_velo_classique", 0),
            data.get("nb_velo_electrique", 0),
            data.get("nb_place_libre", 0),
        ]

        st_apexcharts(options, series, 'donut', '400', 'Disponibilité des vélos')

        # ── Métriques sous le donut ─────────────────────────
        col1, col2, col3 = st.columns(3)
        col1.metric("🚲 Classiques", data.get("nb_velo_classique"))
        col2.metric("⚡ Électriques", data.get("nb_velo_electrique"))
        col3.metric("🅿️ Places libres", data.get("nb_place_libre"))
    
    if semaine_response.status_code == 200:
        semaine = semaine_response.json()  # ← c'est une liste, pas un DataFrame !
        df = pd.DataFrame(semaine)         # ← on convertit ici

        st.subheader(" Tendance sur 7 jours")

        options_line = {
            "chart": {"toolbar": {"show": False}},
            "xaxis": {"categories": df["jour"].tolist()},
            "stroke": {"curve": "smooth", "width": 2},
            "legend": {"show": True, "position": "bottom"},
            "colors": ["#F4A261", "#2A9D8F", "#E76F51"],
        }
        series_line = [
            {"name": " Matin",    "data": df["moyenne_velo_matin"].tolist()},
            {"name": " Après-midi", "data": df["moyenne_velo_aprem"].tolist()},
            {"name": " Soir",     "data": df["moyenne_velo_soir"].tolist()},
        ]
        st_apexcharts(options_line, series_line, 'line', '800', 'Tendance hebdomadaire')


    x = datetime.datetime.now()
    hours = "".join([f"&heure={i}:00" for i in range(x.hour, 24)])

    #hours = "".join([f"&heure={i}:00" for i in range(5, 24)])

    predictions_response = requests.get(f"http://{HOST}:8000/v1/predictions/station?id_station={id_station}{hours}")

    if predictions_response.status_code == 200:
        predictions = predictions_response.json()
        df_pred = pd.DataFrame(predictions["predictions"])  

        options_pred = {
            "chart": {"toolbar": {"show": False}},
            "xaxis": {"categories": df_pred["heure"].tolist()},
            "stroke": {"curve": "smooth", "width": 2},
            "legend": {"show": True, "position": "bottom"},
            "colors": ["#F4A261"],
        }
        series_pred = [
            {"name": "Prédiction", "data": df_pred["prediction_nb_velo"].tolist()},
        ]

        st.subheader("Prédictions du jour")
        st_apexcharts(options_pred, series_pred, 'line', '800', 'Prédictions')


   
            

  

except Exception as e:
    st.error(f" Erreur : {e}")

# ── Bouton retour ──────────────────────────────────
if st.button("⬅️ Retour Accueil"):
    st.switch_page("/app.py")  
