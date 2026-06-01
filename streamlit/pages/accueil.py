import streamlit as st

# ── Titre principal ────────────────────────────────
st.title("🚲 Vélos en libre-service - Paris")


# ── Description ────────────────────────────────────
st.markdown("""
## 📌  Contexte du projet



Ce projet est une solution MLOps complète pour l'analyse et la prédiction de la disponibilité des vélos en libre-service Vélib' à Paris. Il s'appuie sur une architecture containeurisée incluant une API FastAPI, des modèles de Machine Learning, et un pipeline de données automatisé.

🎓 Ce projet a été réalisé dans le cadre du cursus **Data Engineer de LIORA / École des Mines Paris **.


---

## 🎯  Objectifs

Les principaux objectifs du projet sont :

- Nettoyer et structurer les données provenant de l'API Vélib' et d'autres sources
- Réaliser une analyse exploratoire des données (EDA)
- Identifier les tendances temporelles et géographiques
- Visualiser l'activité du réseau Vélib'
- Mettre en place des indicateurs de performance
- Tester des approches de prédiction (disponibilité, saturation, etc.)
""")

st.divider()

