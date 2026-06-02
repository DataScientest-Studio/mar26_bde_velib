from datetime import datetime, timedelta
from datetime import date as date_type
from fastapi import HTTPException, status

from src.api.schemas.statistiques import StatsGlobal, StatsJour
from src.api.services import stations_service
from src.data.Postgre_Request import PostgreRequest 


# --- Stats global (déjà fait) ---
def _dataframe_to_stats_global(df) -> StatsGlobal:
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de contacter la base de données",
        )
    if df.empty or df.iloc[0]["nb_stations_total"] is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucune donnée disponible",
        )

    row = df.iloc[0]
    nb_stations = int(row["nb_stations_total"])
    nb_velos = int(row["nb_velos_disponibles"] or 0)
    nb_libres = int(row["nb_places_libres"] or 0)
    capacite = nb_velos + nb_libres

    return StatsGlobal(
        nb_stations_total=nb_stations,
        nb_stations_actives=nb_stations,
        nb_velos_disponibles=nb_velos,
        nb_places_libres=nb_libres,
        taux_disponibilite=(nb_velos / capacite) if capacite > 0 else 0.0,
        derniere_maj=row["derniere_maj"],
    )


def get_stats_global() -> StatsGlobal:
    df = PostgreRequest.extract_stats_global()
    return _dataframe_to_stats_global(df)


# --- Stats semaine ---
def _dataframe_to_stats_semaine(df) -> list[StatsJour]:
    """Convertit le DataFrame de extract_stats_semaine en liste de StatsJour."""
    if df is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Impossible de contacter la base de données",
        )

    stats: list[StatsJour] = []
    for _, row in df.iterrows():
        stats.append(StatsJour(
            jour=row["jour"],
            moyenne_velo_matin=float(row["moyenne_velo_matin"] or 0),
            moyenne_velo_aprem=float(row["moyenne_velo_aprem"] or 0),
            moyenne_velo_soir=float(row["moyenne_velo_soir"] or 0),
        ))
    return stats


def get_stats_semaine(id_station: int) -> list[StatsJour]:
    # Vérifie que la station existe (lève 404 si non)
    stations_service.get_station(id_station)

    df = PostgreRequest.extract_stats_semaine(id_station)
    return _dataframe_to_stats_semaine(df)
