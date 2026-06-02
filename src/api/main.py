from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.routers import auth, health, stations, predictions, statistiques
import logging

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

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        from src.models.predict import Prediction
        app.state.predictor = Prediction()
        app.state.predictor_is_fake = False
        logger.info("✅ Vrai modèle ML chargé")
    except Exception as e:
        from src.models.fake_predictor import FakePredictor
        app.state.predictor = FakePredictor()
        app.state.predictor_is_fake = True
        logger.warning(f"⚠️ Modèle indisponible ({e}), bascule sur FakePredictor")

    yield
    app.state.predictor = None

app = FastAPI(
    title="API Vélib' Predict",
    version="1.0.0",
    lifespan=lifespan,
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
