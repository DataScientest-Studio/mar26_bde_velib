from datetime import datetime
from pydantic import BaseModel, Field


# --- Proximité ---
class Proximite(BaseModel):
    arret_transport: str
    distance: float = Field(..., description="Distance en mètres")


# --- Météo ---
class Meteo(BaseModel):
    description: str
    temperature: float = Field(..., description="Température en °C")
    humidite: float = Field(..., description="Humidité en %")
    vent: float = Field(..., description="Vitesse du vent en km/h")


# --- Stations ---
class Station(BaseModel):
    id_station: int
    nom_station: str
    longitude: float
    latitude: float
    capacite_totale: int
    proximite: list[Proximite] = []


# --- État ---
class EtatStation(BaseModel):
    id_station: int
    nb_velo: int
    nb_velo_classique: int
    nb_velo_electrique: int
    nb_place_libre: int
    capacite_totale: int
    derniere_maj: datetime
    meteo: Meteo
