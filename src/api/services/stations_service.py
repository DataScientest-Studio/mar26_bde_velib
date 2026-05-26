from datetime import datetime, timezone
from fastapi import HTTPException, status
from src.api.schemas.stations import Station, EtatStation, Proximite, Meteo
from src.data.Postgre_Request import PostgreRequest

def _dataframe_to_stations(df) -> list[Station]:
    """Convertit le DataFrame retourné par extrat_info_station_api en liste de Station."""
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de contacter la base de données",
        )

    stations: dict[int, Station] = {}
    seen_arrets: dict[int, set[str]] = {}  # ← trace les arrnames déjà ajoutés par station

    for _, row in df.iterrows():
        id_station = int(row["id_station"])

        if id_station not in stations:
            stations[id_station] = Station(
                id_station=id_station,
                nom_station=row["name"],
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                capacite_totale=int(row["capacity"]),
                proximite=[],
            )
            seen_arrets[id_station] = set()

        arrname = row["arrname"]
        if arrname not in seen_arrets[id_station]:
            seen_arrets[id_station].add(arrname)
            stations[id_station].proximite.append(
                Proximite(
                    arret_transport=arrname,
                    distance=float(row["distance"]),
                )
            )

    return list(stations.values())

def _dataframe_to_etats(df) -> list[EtatStation]:
    """Convertit le DataFrame de extrat_info_etat_api en liste de EtatStation."""
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de contacter la base de données",
        )

    etats: list[EtatStation] = []

    for _, row in df.iterrows():
        # Météo : LEFT JOIN, donc peut être None
        meteo = None
        if row.get("description") is not None:
            meteo = Meteo(
                description=row["description"],
                temperature=float(row["temperature"]),
                humidite=float(row["humidite"]),
                vent=float(row["vent"]),
            )

        etats.append(EtatStation(
            id_station=int(row["id_station"]),
            nb_velo=int(row["nb_velo"]),
            nb_velo_classique=int(row["nb_velo_classique"]),
            nb_velo_electrique=int(row["nb_velo_electrique"]),
            nb_place_libre=int(row["nb_place_libre"]),
            capacite_totale=int(row["capacite_totale"]),
            derniere_maj=row["derniere_maj"],
            meteo=meteo,
        ))

    return etats

def list_stations() -> list[Station]:
    df = PostgreRequest.extrat_info_station_api()
    return _dataframe_to_stations(df)


def get_station(id_station: int) -> Station:
    df = PostgreRequest.extrat_info_station_api(id_station=id_station)

    stations = _dataframe_to_stations(df)

    if not stations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station {id_station} introuvable",
        )

    return stations[0]


def _fake_meteo() -> Meteo:
    # --- Données factices (à remplacer par les méthode de Belkacem) ---
    return Meteo(description="Ensoleillé", temperature=22.5, humidite=60.0, vent=10.0)


def get_etat_station(id_station: int) -> EtatStation:
    df = PostgreRequest.extrat_info_etat_api(id_station=id_station)
    etats = _dataframe_to_etats(df)

    if not etats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station {id_station} introuvable ou pas de données récentes",
        )

    return etats[0]


def list_etats() -> list[EtatStation]:
    df = PostgreRequest.extrat_info_etat_api()
    return _dataframe_to_etats(df)
