from fastapi import APIRouter, Depends
from src.api.schemas.stations import Station, EtatStation
from src.api.services import stations_service
from src.api.dependencies import get_current_user

router = APIRouter(
    prefix="/v1",
    tags=["Stations"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/stations",
    response_model=list[Station],
    summary="Liste toutes les stations",
    description="Retourne l'ensemble des stations Vélib' avec leurs informations "
                "statiques (position, capacité, transports à proximité).",
    responses={
        401: {"description": "Token JWT manquant ou invalide"},
    },
)
def get_stations():
    """Liste toutes les stations."""
    return stations_service.list_stations()


@router.get(
    "/stations/etats",
    response_model=list[EtatStation],
    summary="État temps réel de toutes les stations",
)
def get_all_etats():
    """État en temps réel de toutes les stations."""
    return stations_service.list_etats()


@router.get(
    "/stations/{id_station}/etat",
    response_model=EtatStation,
    summary="État temps réel d'une station",
    description="Retourne le nombre de vélos disponibles (classiques et électriques), "
                "les places libres et la météo actuelle à la station.",
    responses={404: {"description": "Station introuvable"}},
)
def get_etat(id_station: int):
    """État en temps réel d'une station."""
    return stations_service.get_etat_station(id_station)

@router.get(
    "/stations/{id_station}",
    response_model=Station,
    summary="Détail d'une station",
    responses={
        404: {"description": "Station introuvable"},
        401: {"description": "Token JWT manquant ou invalide"},
    },
)
def get_station_by_id(id_station: int):
    """Détail d'une station."""
    return stations_service.get_station(id_station)