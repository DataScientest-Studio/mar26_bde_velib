import streamlit as st
import requests
import pandas as pd
import pydeck as pdk
import time
import datetime

st.title(" Dashboard - Stations")


try:
    response = requests.get("http://localhost:8000/v1/stations")

    if response.status_code == 200:
        data = response.json()
        df = pd.DataFrame(data)

        # ── Métriques ──────────────────────────────────────
        st.metric("Nombre de stations", len(df))

        # ── Carte Interactive ───────────────────────────────
        st.subheader(" Carte des stations")

        if "latitude" in df.columns and "longitude" in df.columns:
            df_map = df.rename(columns={"latitude": "lat", "longitude": "lon"})
        elif "lat" in df.columns and "lon" in df.columns:
            df_map = df.copy()
        else:
            st.warning(" Pas de colonnes latitude/longitude trouvées")
            df_map = None

        if df_map is not None:

            layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_map,
                get_position=["lon", "lat"],
                get_color=[255, 0, 0, 180],
                get_radius=100,
                radius_min_pixels=4,
                radius_max_pixels=15,
                pickable=True,
                auto_highlight=True,
            )

            view_state = pdk.ViewState(
                latitude=df_map["lat"].mean(),
                longitude=df_map["lon"].mean(),
                zoom=10,
                pitch=0,
            )

            tooltip = {
                "html": """
                    <b>🚉 Station :</b> {nom_station} <br>
                    <b>📍 Lat :</b> {lat} <br>
                    <b>📍 Lon :</b> {lon} <br>
                """,
                "style": {
                    "backgroundColor": "steelblue",
                    "color": "white",
                    "fontSize": "14px",
                    "padding": "10px"
                }
            }
            clicked = st.pydeck_chart(
                pdk.Deck(
                    layers=[layer],
                    initial_view_state=view_state,
                    tooltip=tooltip,
                    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
                ),
                on_select="rerun",
                selection_mode="single-object",
            )

            
            if clicked and "objects" in clicked.selection and clicked.selection["objects"]:
                layer_objects = clicked.selection["objects"].get("ScatterplotLayer", [])
                if layer_objects:
                    obj = layer_objects[0]
                    
                    # On stocke l'info dans le session_state
                    st.session_state["id_station"] = obj["id_station"]
                    
                    # On affiche un message rapide et on force le changement de page immédiat
                    st.toast(f"Chargement de la station : {obj['nom_station']}...")
                    st.switch_page("pages/station.py")
                        


        # ── Tableau cliquable ───────────────────────────────
        st.subheader(" Sélectionnez une station")

        cols = [c for c in ["id_station", "nom_station", "lat", "lon"] if c in df_map.columns]

        selected = st.dataframe(
            df_map[cols],
            use_container_width=True,
            on_select="rerun",
            selection_mode="single-row",
        )

        rows = selected.selection.get("rows", [])
        if rows:
            row = df_map.iloc[rows[0]]
            st.session_state["id_station"] = row["id_station"]
            nom = row["nom_station"]

            st.success(f" Station sélectionnée : {nom}")
            st.switch_page("pages/station.py")






    else:
        st.error(f" Erreur API : {response.status_code}")

except requests.exceptions.ConnectionError:
    st.error(" Impossible de se connecter à l'API (localhost:8000)")

except Exception as e:
    st.error(f" Erreur inattendue : {e}")
