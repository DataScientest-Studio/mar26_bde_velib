import streamlit as st
import pandas as pd
import requests

st.title("Statistiques de la semaine")

# 0. Récupération de l'ID de la station sauvegardé en session
id_station = st.session_state.get("id_station")


if id_station is not None:
    try:
        # 1. Appel de l'API
        
        url = f"http://localhost:8000/v1/statistiques/station/{id_station}/semaine"
        semaine_response = requests.get(url)

        if semaine_response.status_code == 200:
            # 2. Conversion du JSON de la réponse en DataFrame (CORRIGÉ ICI)
            data_json = semaine_response.json()
            df_large = pd.DataFrame(data_json)

            # Sécurité au cas où l'API renvoie une liste vide pour cette station
            if not df_large.empty:
                
                # 3. Transformation pour le graphique (Format Large -> Format Long)
                df_long = df_large.melt(
                    id_vars=["jour"], 
                    value_vars=["moyenne_velo_matin", "moyenne_velo_aprem", "moyenne_velo_soir"],
                    var_name="Moment",
                    value_name="Moyenne"
                )

                # Nettoyage des étiquettes de légende
                df_long["Moment"] = df_long["Moment"].str.replace("moyenne_velo_", "").str.capitalize()

                # 4. Affichage du graphique horizontal
                st.bar_chart(
                    df_long, 
                    y="Moyenne",       
                    x="jour",          
                    color="Moment",    
                    horizontal=True
                )
                
            else:
                st.info("Aucune donnée disponible pour cette station cette semaine.")
        else:
            st.error(f"❌ Erreur API ({semaine_response.status_code})")

    except requests.exceptions.ConnectionError:
        st.error("Impossible de joindre l'API backend.")
else:
    st.warning("⚠️ Aucune station n'a été sélectionnée. Retourne sur la carte.")
    if st.button("🗺️ Voir la carte"):
        st.switch_page("app.py") # ou le nom de ton fichier principal





#st.title("🔍 Recherche de Stations")

st.text("🔍 Recherche de Stations")
col1, col2 = st.columns([4, 1])

with col1:
    # Le champ de texte (input)
    query = st.text_input(
        "Rechercher une station", 
        placeholder="Entrez le nom d'une station...",
        label_visibility="collapsed" # Masque le texte d'aide pour un look plus épuré
    )

with col2:
    # Le bouton de recherche (aligné verticalement grâce au petit espace vide optionnel)
    st.write("") 
    bouton_recherche = st.button("🔍 Rechercher", use_container_width=True)

# 2. Déclenchement de l'action
if bouton_recherche or query:
    if query:
        st.success(f"🔎 Résultat pour la recherche : **{query}**")
        st.session_state["nom"] = query

        st.switch_page("pages/metro.py")
        # C'est ici que tu appelleras ton API, ex: requests.get(f"http://localhost:8000/v1/stations/search?q={query}")
    else:
        st.warning("⚠️ Veuillez écrire quelque chose avant de rechercher.")