from datetime import date as date_type, datetime, timedelta
from fastapi import HTTPException, status
from src.api.schemas.predictions import (
    PredictionStation, PredictionMetro, StationProche,
    PredictionTrajet, StationDepart, StationArrivee,
)
from src.api.services import stations_service
from src.data.Postgre_Request import PostgreRequest


def predict_station(predictor, id_station: int, heure: str,date_: date_type | None) -> PredictionStation:
    """Prédiction pour UNE station à UNE heure."""
    # Vérifie que la station existe (lève 404 sinon)
    stations_service.get_station(id_station)

    if date_ is None:
        date_ = date_type.today()

    try:
        results = predictor.prediction_station(
            idstation=id_station,
            heures=[heure],
            date=date_.strftime("%Y-%m-%d"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la prédiction : {e}",
        )

    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucune prédiction pour la station {id_station}",
        )

    r = results[0]
    return PredictionStation(
        id_station=int(r["id_station"]),
        heure=r["heure"],
        date=r["date"],
        prediction_nb_velo=int(r["prediction_nb_velo"]),
    )


def predict_metro(
    predictor,
    arret_transport: str,
    heure: str,
    date_: date_type | None,
) -> PredictionMetro:
    if date_ is None:
        date_ = date_type.today()

    if arret_transport.isdigit():
        stations_proches = _find_stations_near_metro_by_id(int(arret_transport))
    else:
        stations_proches = _find_stations_near_metro_by_name(arret_transport)

    heures = []
    heures.append(heure)

    if not stations_proches:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Aucune station trouvée près de '{arret_transport}'",
        )

    stations = []
    for s in stations_proches:
        result = predictor.prediction_station(s["id_station"], heures, date_)

        stations.append(
            StationProche(
                id_station=s["id_station"],
                nom_station=s["nom_station"],
                distance_metres=s["distance"],
                heure=heure,
                prediction_nb_velo=result[0]["prediction_nb_velo"],
            )
        )

    return PredictionMetro(stations=stations)



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

def _find_stations_near_metro_by_name(nom_arret: str) -> list[dict]:
    """Stations Vélib' proches d'un arrêt de transport (recherche par nom)."""
    df = PostgreRequest.extrat_info_proximiter(
        id_arret_transport=None,
        nom_arret_transport=nom_arret,
    )
    return _proximity_df_to_list(df)


def _find_stations_near_metro_by_id(id_arret: int) -> list[dict]:
    """Stations Vélib' proches d'un arrêt de transport (recherche par ID)."""
    df = PostgreRequest.extrat_info_proximiter(
        id_arret_transport=id_arret,
        nom_arret_transport=None,
    )
    return _proximity_df_to_list(df)


def _proximity_df_to_list(df) -> list[dict]:
    if df is None or df.empty:
        return []

    # Supprime les colonnes en doublon (garde la 1ère occurrence)
    df = df.loc[:, ~df.columns.duplicated()]

    df = df.sort_values("distance").drop_duplicates(subset=["id_station"])

    return [
        {
            "id_station": int(row["id_station"]),
            "nom_station": row["name"],
            "distance": float(row["distance"]),
        }
        for _, row in df.iterrows()
    ]