from __future__ import annotations

import requests
import streamlit as st

st.set_page_config(page_title="Vélib Dashboard", layout="wide")
API_URL = st.sidebar.text_input("URL API", value="http://api:8000")
st.title("Projet Vélib' — Démo API + Dashboard")

page = st.sidebar.radio("Page", ["Prédiction ML", "KPIs réseau"])

if page == "Prédiction ML":
    st.subheader("Prédiction +2h")
    with st.form("predict_form"):
        station_id = st.text_input("Station ID", value="station-demo")
        hour = st.slider("Heure", 0, 23, 8)
        day_of_week = st.slider("Jour de semaine", 0, 6, 2)
        capacity = st.number_input("Capacité", 0, 100, 30)
        num_bikes_available = st.number_input("Vélos dispo", 0, 100, 10)
        num_docks_available = st.number_input("Bornes libres", 0, 100, 20)
        num_ebikes_available = st.number_input("VAE", 0, 100, 3)
        mechanical_bikes = st.number_input("Mécaniques", 0, 100, 7)
        submitted = st.form_submit_button("Prédire")
    if submitted:
        payload = {
            "station_id": station_id,
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": int(day_of_week in (5, 6)),
            "capacity": capacity,
            "occupancy_rate": (num_bikes_available / capacity) if capacity else 0,
            "num_bikes_available": num_bikes_available,
            "num_docks_available": num_docks_available,
            "num_ebikes_available": num_ebikes_available,
            "mechanical_bikes": mechanical_bikes,
            "bikes_lag_1": num_bikes_available,
            "bikes_lag_3": num_bikes_available,
            "bikes_lag_6": num_bikes_available,
            "docks_lag_1": num_docks_available,
            "docks_lag_3": num_docks_available,
            "docks_lag_6": num_docks_available,
        }
        response = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
        if response.ok:
            result = response.json()
            st.success(f"Prévision pour {result['station_id']} : {result['predicted_bikes']} vélos à {result['horizon']}")
        else:
            st.error(response.text)
else:
    st.subheader("KPIs réseau")
    response = requests.get(f"{API_URL}/stats", timeout=30)
    if response.ok:
        data = response.json()
        col1, col2, col3 = st.columns(3)
        col1.metric("Taux disponibilité réseau", f"{data['network_availability_rate']}%")
        col2.metric("Stations suivies", data["stations_count"])
        col3.metric("Vélos disponibles", data["bikes_available_total"])
        st.dataframe(data["critical_stations"])
    else:
        st.error(response.text)
