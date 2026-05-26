from fastapi import FastAPI
from src.api.routers import auth, health, stations, predictions, statistiques

tags_metadata = [
    {
        "name": "Health",
        "description": "Vérification de l'état de l'API.",
    },
    {
        "name": "Auth",
        "description": "Authentification JWT. Récupérez un token via `/auth/login` "
                       "puis utilisez-le dans le header `Authorization: Bearer <token>`.",
    },
    {
        "name": "Stations",
        "description": "Informations sur les stations Vélib' et leur état en temps réel.",
    },
    {
        "name": "Predictions",
        "description": "Prédictions de disponibilité basées sur un modèle de Machine Learning.",
    },
    {
        "name": "Statistiques",
        "description": "Statistiques globales et tendances historiques du réseau.",
    },
]

app = FastAPI(
    title="API Vélib' Predict",
    version="1.0.0",
    description="""
API de prédiction de disponibilité des stations Vélib'.

## Fonctionnalités

* **Stations** : consultation des stations et de leur état en temps réel
* **Prédictions** : disponibilité future par station, métro ou trajet
* **Statistiques** : agrégats globaux et tendances hebdomadaires

## Authentification

Tous les endpoints (hors `/auth/login` et `/health`) nécessitent un token JWT.
    """
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(stations.router)
app.include_router(predictions.router)
app.include_router(statistiques.router)
