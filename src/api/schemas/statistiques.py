from datetime import date as date_type, datetime
from pydantic import BaseModel, Field


class StatsGlobal(BaseModel):
    nb_stations_total: int
    nb_stations_actives: int
    nb_velos_disponibles: int
    nb_places_libres: int
    taux_disponibilite: float = Field(..., ge=0, le=1, description="Entre 0 et 1")
    derniere_maj: datetime


class StatsJour(BaseModel):
    jour: date_type
    moyenne_velo_matin: float
    moyenne_velo_aprem: float
    moyenne_velo_soir: float
