from datetime import date as date_type, datetime, timedelta
from fastapi import HTTPException, status
from src.api.schemas.predictions import (
    PredictionStation, PredictionMetro, StationProche,
    PredictionTrajet, StationDepart, StationArrivee,
)
from src.api.services import stations_service


def predict_station(id_station: int, heure: str, date_: date_type | None) -> PredictionStation:
    # Vérifie que la station existe
    stations_service.get_station(id_station)

    if date_ is None:
        date_ = date_type.today()

    # TODO: brancher le vrai modèle ML
    prediction = _fake_prediction(id_station, heure)

    return PredictionStation(
        id_station=id_station,
        heure=heure,
        date=date_,
        prediction_nb_velo=prediction,
    )


def predict_metro(arret_transport: str, heure: str, date_: date_type | None) -> PredictionMetro:
    if date_ is None:
        date_ = date_type.today()

    # TODO: chercher les stations proches du métro en BDD
    # Pour l'instant, on simule
    stations_proches = _find_stations_near_metro(arret_transport)

    if not stations_proches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucune station trouvée près de '{arret_transport}'",
        )

    return PredictionMetro(
        stations=[
            StationProche(
                id_station=s["id_station"],
                nom_station=s["nom_station"],
                distance_metres=s["distance"],
                heure=heure,
                prediction_nb_velo=_fake_prediction(s["id_station"], heure),
            )
            for s in stations_proches
        ]
    )


def predict_trajet(
    heure_depart: str,
    date_: date_type | None,
    lat_depart: float | None = None,
    lon_depart: float | None = None,
    lat_arrivee: float | None = None,
    lon_arrivee: float | None = None,
    id_station_depart: int | None = None,
    id_station_arrivee: int | None = None,
) -> PredictionTrajet:
    if date_ is None:
        date_ = date_type.today()

    # Résolution départ
    if id_station_depart is None:
        if lat_depart is None or lon_depart is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fournir id_station_depart OU (lat_depart + lon_depart)",
            )
        id_station_depart, dist_dep = _nearest_station(lat_depart, lon_depart)
    else:
        dist_dep = 0.0

    # Résolution arrivée
    if id_station_arrivee is None:
        if lat_arrivee is None or lon_arrivee is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Fournir id_station_arrivee OU (lat_arrivee + lon_arrivee)",
            )
        id_station_arrivee, dist_arr = _nearest_station(lat_arrivee, lon_arrivee)
    else:
        dist_arr = 0.0

    station_dep = stations_service.get_station(id_station_depart)
    station_arr = stations_service.get_station(id_station_arrivee)
    etat_arr = stations_service.get_etat_station(id_station_arrivee)

    # TODO: calculer une vraie heure d'arrivée (distance + vitesse moyenne)
    heure_arrivee = _add_minutes(heure_depart, 15)

    return PredictionTrajet(
        station_depart=StationDepart(
            id_station=station_dep.id_station,
            nom_station=station_dep.nom_station,
            distance_metres=dist_dep,
            prediction_nb_velo=_fake_prediction(id_station_depart, heure_depart),
        ),
        station_arrivee=StationArrivee(
            id_station=station_arr.id_station,
            nom_station=station_arr.nom_station,
            distance_metres=dist_arr,
            nb_place_libre=etat_arr.nb_place_libre,
            prediction_nb_place_libre=_fake_prediction(id_station_arrivee, heure_arrivee),
        ),
        heure_arrivee_estimee=heure_arrivee,
    )


# --- Helpers factices (à remplacer par la vraie logique ML/BDD) ---
def _fake_prediction(id_station: int, heure: str) -> int:
    return (id_station * 3 + int(heure.split(":")[0])) % 20


def _find_stations_near_metro(arret: str) -> list[dict]:
    # Simulation : retourne quelques stations factices
    return [
        {"id_station": 1, "nom_station": "République", "distance": 50.0},
        {"id_station": 2, "nom_station": "Bastille", "distance": 200.0},
    ]


def _nearest_station(lat: float, lon: float) -> tuple[int, float]:
    # TODO: vraie recherche géographique (PostGIS, haversine...)
    return (1, 120.0)


def _add_minutes(heure: str, minutes: int) -> str:
    h, m = map(int, heure.split(":"))
    total = h * 60 + m + minutes
    return f"{(total // 60) % 24:02d}:{total % 60:02d}"
