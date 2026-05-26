from datetime import datetime, timezone
from fastapi import HTTPException, status
from src.api.schemas.stations import Station, EtatStation, Proximite, Meteo


# --- Données factices (à remplacer par les méthode de Belkacem) ---
_STATIONS_DB: dict[int, Station] = {
    1: Station(
        id_station=1,
        nom_station="République",
        longitude=2.3635,
        latitude=48.8676,
        capacite_totale=30,
        proximite=[
            Proximite(arret_transport="Métro République", distance=50.0),
        ],
    ),
    2: Station(
        id_station=2,
        nom_station="Bastille",
        longitude=2.3692,
        latitude=48.8532,
        capacite_totale=40,
        proximite=[
            Proximite(arret_transport="Métro Bastille", distance=30.0),
        ],
    ),
}


def list_stations() -> list[Station]:
    return list(_STATIONS_DB.values())


def get_station(id_station: int) -> Station:
    station = _STATIONS_DB.get(id_station)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station {id_station} introuvable",
        )
    return station


def _fake_meteo() -> Meteo:
    # --- Données factices (à remplacer par les méthode de Belkacem) ---
    return Meteo(description="Ensoleillé", temperature=22.5, humidite=60.0, vent=10.0)


def get_etat_station(id_station: int) -> EtatStation:
    station = get_station(id_station)  # Lève 404 si inconnue
    # --- Données factices (à remplacer par les méthode de Belkacem) ---
    nb_classique, nb_elec = 8, 5
    nb_velo = nb_classique + nb_elec
    return EtatStation(
        id_station=station.id_station,
        nb_velo=nb_velo,
        nb_velo_classique=nb_classique,
        nb_velo_electrique=nb_elec,
        nb_place_libre=station.capacite_totale - nb_velo,
        capacite_totale=station.capacite_totale,
        derniere_maj=datetime.now(timezone.utc),
        meteo=_fake_meteo(),
    )


def list_etats() -> list[EtatStation]:
    return [get_etat_station(sid) for sid in _STATIONS_DB.keys()]
