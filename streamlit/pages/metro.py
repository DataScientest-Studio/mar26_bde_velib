import streamlit as st
import requests
import pandas as pd
from datetime import date



st.title(f"Information metro ")

st.text("🔍 Recherche de Stations")

col1, col2, col3, col4 = st.columns([4, 2, 2, 1])

with col1:
    query = st.text_input(
        "Rechercher une station",
        placeholder="Entrez le nom d'une station...",
        label_visibility="collapsed"
    )

with col2:
    heure = st.time_input(
        "Heure",
        label_visibility="collapsed",
        step=1800
    )
    heure_str = heure.strftime("%H:%M")

with col3:
    date_choisie = st.date_input(
        "Date",
        value=date.today(),
        label_visibility="collapsed"
    )
    date_str = date_choisie.strftime("%Y-%m-%d")

with col4:
    st.write("")
    bouton_recherche = st.button("🔍 Rechercher", use_container_width=True)

# ── Déclenchement ──────────────────────────────────
if bouton_recherche or query:
    if query:
        url = requests.get(
            f"http://localhost:8000/v1/predictions/metro",
            params={"arret_transport": query, "heure": heure_str, "date": date_str}
        )

        if url.status_code == 200:
            st.success(f"🔎 Résultat pour : **{query}** le **{date_str}** à **{heure_str}**")
            st.session_state["nom"] = query

            metro = url.json()
            df_metro = pd.DataFrame(metro["stations"])
            st.dataframe(
                df_metro[["nom_station", "distance_metres", "heure", "prediction_nb_velo"]],
                use_container_width=True
            )
        elif url.status_code == 404:
            st.error("❌ Station inconnue")
        else:
            st.error(f"❌ Erreur API : {url.status_code}")

    else:
        st.warning("⚠️ Veuillez écrire quelque chose avant de rechercher.")