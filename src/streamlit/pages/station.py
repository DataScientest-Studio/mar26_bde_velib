import streamlit as st
import requests
import pandas as pd
from streamlit_apexjs import st_apexcharts
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
HOST = os.getenv("API_HOST")

# ── Auth ───────────────────────────────────────────
auth = requests.post(f"http://{HOST}:8000/auth/login", data={
    "username": os.getenv("API_USER"),
    "password": os.getenv("API_PASSWORD")
})
access_token = auth.json()["access_token"]
headers = {"Authorization": f"Bearer {access_token}"}

# ── Vérif session ──────────────────────────────────
id_station = st.session_state.get("id_station")
if not id_station:
    st.error("Aucune station sélectionnée")
    st.stop()

st.title(f"Station #{id_station}")

# ══════════════════════════════════════════════════
# PHASE 1 : Tous les appels API
# ══════════════════════════════════════════════════
try:
    with st.spinner("Chargement des données..."):
        x = datetime.datetime.now()
        hours = "".join([f"&heure={i}:00" for i in range(x.hour, 24)])

        r_station = requests.get(f"http://{HOST}:8000/v1/stations/{id_station}", headers=headers)
        r_etat    = requests.get(f"http://{HOST}:8000/v1/stations/{id_station}/etat", headers=headers)
        r_semaine = requests.get(f"http://{HOST}:8000/v1/statistiques/station/{id_station}/semaine", headers=headers)
        r_pred    = requests.get(f"http://{HOST}:8000/v1/predictions/station?id_station={id_station}{hours}", headers=headers)

    # ══════════════════════════════════════════════
    # PHASE 2 : Affichage après réception
    # ══════════════════════════════════════════════
    print(f" station : {r_station.status_code} - etat : {r_etat.status_code}  - sem : {r_semaine.status_code}  - pred : {r_pred.status_code}   ")
    # ── Infos station ──────────────────────────────
    if r_station.status_code == 200:
        station = r_station.json()
        st.subheader(station.get("nom_station", "Nom inconnu"))
        st.write("📍 Latitude :",  station.get("latitude"))
        st.write("📍 Longitude :", station.get("longitude"))

    # ── Disponibilité ──────────────────────────────
    if r_etat.status_code == 200:
        etat = r_etat.json()
        st.subheader("Disponibilité")
        st_apexcharts(
            {
                "chart": {"toolbar": {"show": False}},
                "labels": ["Vélos classiques", "Vélos électriques", "Places libres"],
                "legend": {"show": True, "position": "bottom"},
                "colors": ["#316DDD", "#45D628", "#D62828"],
            },
            [etat.get("nb_velo_classique", 0), etat.get("nb_velo_electrique", 0), etat.get("nb_place_libre", 0)],
            'donut', '400', 'Disponibilité des vélos'
        )
        col1, col2, col3 = st.columns(3)
        col1.metric("🚲 Classiques",    etat.get("nb_velo_classique"))
        col2.metric("⚡ Électriques",   etat.get("nb_velo_electrique"))
        col3.metric("🅿️ Places libres", etat.get("nb_place_libre"))

    # ── Tendance 7 jours ───────────────────────────
    if r_semaine.status_code == 200:
        df_sem = pd.DataFrame(r_semaine.json())
        st.subheader("Tendance sur 7 jours")
        st_apexcharts(
            {
                "chart": {"toolbar": {"show": False}},
                "xaxis": {"categories": df_sem["jour"].tolist()},
                "stroke": {"curve": "smooth", "width": 2},
                "legend": {"show": True, "position": "bottom"},
                "colors": ["#F4A261", "#2A9D8F", "#E76F51"],
            },
            [
                {"name": "Matin",      "data": df_sem["moyenne_velo_matin"].tolist()},
                {"name": "Après-midi", "data": df_sem["moyenne_velo_aprem"].tolist()},
                {"name": "Soir",       "data": df_sem["moyenne_velo_soir"].tolist()},
            ],
            'line', '800', 'Tendance hebdomadaire'
        )

    # ── Prédictions ────────────────────────────────
    print(f"r_pred.status_code {r_pred.status_code} {r_pred.status_code == 200:}")
    if r_pred.status_code == 200:
        data_pred = r_pred.json()
    
        # Une seule prédiction (dict) ou plusieurs (liste)
        if isinstance(data_pred, list):
            df_pred = pd.DataFrame(data_pred)
        else:
            df_pred = pd.DataFrame([data_pred])
        
        print(f"df_pred : {df_pred}")
        
        st.subheader("Prédictions du jour")
        st_apexcharts(
            {
                "chart": {"toolbar": {"show": False}},
                "xaxis": {"categories": df_pred["heure"].tolist()},
                "stroke": {"curve": "smooth", "width": 2},
                "legend": {"show": True, "position": "bottom"},
                "colors": ["#F4A261"],
            },
            [{"name": "Prédiction", "data": df_pred["prediction_nb_velo"].tolist()}],
            'line', '800', 'Prédictions'
        )
    else:
        st.warning(f"Prédictions indisponibles (code {r_pred.status_code})")

except Exception as e:
    st.error(f"Erreur : {e}")
