from datetime import date as date_type
from pydantic import BaseModel, Field, model_validator
from typing import Self


# --- Prédiction station ---
class PredictionHoraire(BaseModel):
    heure: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    prediction_nb_velo: int


class PredictionStation(BaseModel):
    id_station: int
    date: date_type
    predictions: list[PredictionHoraire]


# --- Prédiction métro ---
class StationProche(BaseModel):
    id_station: int
    nom_station: str
    distance_metres: float
    predictions: list[PredictionHoraire]   # ← idem, liste


class PredictionMetro(BaseModel):
    stations: list[StationProche]


# --- Prédiction trajet ---
class StationDepart(BaseModel):
    id_station: int
    nom_station: str
    distance_metres: float
    prediction_nb_velo: int


class StationArrivee(BaseModel):
    id_station: int
    nom_station: str
    distance_metres: float
    nb_place_libre: int
    prediction_nb_place_libre: int


class PredictionTrajet(BaseModel):
    station_depart: StationDepart
    station_arrivee: StationArrivee
    heure_arrivee_estimee: str
