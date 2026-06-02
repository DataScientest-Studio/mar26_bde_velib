import sys
from unittest.mock import patch, MagicMock
from datetime import datetime, date

import pytest

sys.modules['psycopg2'] = MagicMock()

from fastapi import HTTPException
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import get_current_user
from src.api.schemas.auth import User
from src.api.schemas.stations import Station, EtatStation, Meteo
from src.api.schemas.statistiques import StatsGlobal, StatsJour
from src.api.schemas.predictions import (
    PredictionStation, PredictionMetro, StationProche,
    PredictionTrajet, StationDepart, StationArrivee,
)
from src.models.fake_predictor import FakePredictor


def _fake_user():
    return User(username="test_user")


# ── Données fictives ──────────────────────────────────────────────────────────
FAKE_STATION = Station(id_station=1, nom_station="République", longitude=2.36,
                       latitude=48.86, capacite_totale=20, proximite=[])

FAKE_STATION_2 = Station(id_station=2, nom_station="Bastille", longitude=2.37,
                         latitude=48.85, capacite_totale=15, proximite=[])

FAKE_ETAT = EtatStation(
    id_station=1, nb_velo=10, nb_velo_classique=7, nb_velo_electrique=3,
    nb_place_libre=10, capacite_totale=20,
    derniere_maj=datetime(2025, 1, 15, 8, 0, 0),
    meteo=Meteo(description="Ensoleillé", temperature=12.0, humidite=60.0, vent=15.0),
)

FAKE_ETAT_2 = EtatStation(
    id_station=2, nb_velo=5, nb_velo_classique=3, nb_velo_electrique=2,
    nb_place_libre=10, capacite_totale=15,
    derniere_maj=datetime(2025, 1, 15, 8, 0, 0),
    meteo=Meteo(description="Nuageux", temperature=10.0, humidite=70.0, vent=20.0),
)

FAKE_STATS_GLOBAL = StatsGlobal(
    nb_stations_total=100, nb_stations_actives=90,
    nb_velos_disponibles=500, nb_places_libres=300,
    taux_disponibilite=0.62, derniere_maj=datetime(2025, 1, 15, 8, 0, 0),
)

FAKE_STATS_SEMAINE = [
    StatsJour(jour=date(2025, 1, 9),  moyenne_velo_matin=8.0, moyenne_velo_aprem=5.0, moyenne_velo_soir=3.0),
    StatsJour(jour=date(2025, 1, 10), moyenne_velo_matin=7.0, moyenne_velo_aprem=6.0, moyenne_velo_soir=4.0),
    StatsJour(jour=date(2025, 1, 11), moyenne_velo_matin=6.0, moyenne_velo_aprem=4.0, moyenne_velo_soir=2.0),
    StatsJour(jour=date(2025, 1, 12), moyenne_velo_matin=9.0, moyenne_velo_aprem=7.0, moyenne_velo_soir=5.0),
    StatsJour(jour=date(2025, 1, 13), moyenne_velo_matin=5.0, moyenne_velo_aprem=3.0, moyenne_velo_soir=1.0),
    StatsJour(jour=date(2025, 1, 14), moyenne_velo_matin=4.0, moyenne_velo_aprem=2.0, moyenne_velo_soir=0.0),
    StatsJour(jour=date(2025, 1, 15), moyenne_velo_matin=3.0, moyenne_velo_aprem=1.0, moyenne_velo_soir=0.0),
]

FAKE_PREDICTION_STATION = PredictionStation(
    id_station=1, heure="08:30", date=date(2025, 1, 15), prediction_nb_velo=12
)

FAKE_PREDICTION_METRO = PredictionMetro(stations=[
    StationProche(id_station=1, nom_station="République", distance_metres=50.0,  heure="08:30", prediction_nb_velo=12),
    StationProche(id_station=2, nom_station="Bastille",   distance_metres=200.0, heure="08:30", prediction_nb_velo=8),
])

FAKE_PREDICTION_TRAJET = PredictionTrajet(
    station_depart=StationDepart(id_station=1, nom_station="République", distance_metres=0.0, prediction_nb_velo=12),
    station_arrivee=StationArrivee(id_station=2, nom_station="Bastille", distance_metres=0.0, nb_place_libre=10, prediction_nb_place_libre=8),
    heure_arrivee_estimee="08:45",
)


# ── Fixture client UNIQUE ─────────────────────────────────────────────────────
@pytest.fixture
def client():
    def _not_found(msg="Station introuvable"):
        raise HTTPException(status_code=404, detail=msg)

    STATIONS = {1: FAKE_STATION, 2: FAKE_STATION_2}
    ETATS    = {1: FAKE_ETAT,    2: FAKE_ETAT_2}
    STATS    = {1: FAKE_STATS_SEMAINE, 2: FAKE_STATS_SEMAINE}

    def _predict_station(predictor, id_station, heure, date=None):
        if id_station not in STATIONS:
            _not_found()
        return FAKE_PREDICTION_STATION

    def _predict_trajet(predictor, heure_depart, date_=None,
                        lat_depart=None, lon_depart=None,
                        lat_arrivee=None, lon_arrivee=None,
                        id_station_depart=None, id_station_arrivee=None):
        has_depart  = (lat_depart  is not None and lon_depart  is not None) or id_station_depart  is not None
        has_arrivee = (lat_arrivee is not None and lon_arrivee is not None) or id_station_arrivee is not None
        if not has_depart or not has_arrivee:
            raise HTTPException(status_code=422, detail="Paramètres départ/arrivée manquants")
        return FAKE_PREDICTION_TRAJET

    app.dependency_overrides[get_current_user] = _fake_user
    app.state.predictor = FakePredictor()
    app.state.predictor_is_fake = True

    with \
        patch("src.api.services.stations_service.list_stations",
              return_value=[FAKE_STATION, FAKE_STATION_2]), \
        patch("src.api.services.stations_service.list_etats",
              return_value=[FAKE_ETAT, FAKE_ETAT_2]), \
        patch("src.api.services.stations_service.get_station",
              side_effect=lambda id_: STATIONS.get(id_) or _not_found()), \
        patch("src.api.services.stations_service.get_etat_station",
              side_effect=lambda id_: ETATS.get(id_) or _not_found()), \
        patch("src.api.services.statistiques_service.get_stats_global",
              return_value=FAKE_STATS_GLOBAL), \
        patch("src.api.services.statistiques_service.get_stats_semaine",
              side_effect=lambda id_: STATS.get(id_) or _not_found()), \
        patch("src.api.services.predictions_service.predict_station",
              side_effect=_predict_station), \
        patch("src.api.services.predictions_service.predict_metro",
              side_effect=lambda *args, **kwargs: FAKE_PREDICTION_METRO), \
        patch("src.api.services.predictions_service.predict_trajet",
              side_effect=_predict_trajet):
        yield TestClient(app)

    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    return TestClient(app)
