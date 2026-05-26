from datetime import date as date_type, datetime, timedelta, timezone
from src.api.schemas.statistiques import StatsGlobal, StatsJour
from src.api.services import stations_service


def get_stats_global() -> StatsGlobal:
    # TODO: requêtes BDD agrégées
    etats = stations_service.list_etats()

    nb_total = len(etats)
    nb_velos = sum(e.nb_velo for e in etats)
    nb_libres = sum(e.nb_place_libre for e in etats)
    capacite = sum(e.capacite_totale for e in etats)

    return StatsGlobal(
        nb_stations_total=nb_total,
        nb_stations_actives=nb_total,  # TODO: filtrer celles "en panne"
        nb_velos_disponibles=nb_velos,
        nb_places_libres=nb_libres,
        taux_disponibilite=nb_velos / capacite if capacite > 0 else 0.0,
        derniere_maj=datetime.now(timezone.utc),
    )


def get_stats_semaine(id_station: int) -> list[StatsJour]:
    # Vérifie que la station existe
    stations_service.get_station(id_station)

    # TODO: requête BDD historique
    today = date_type.today()
    return [
        StatsJour(
            jour=today - timedelta(days=i),
            moyenne_velo_matin=10.0 + i,
            moyenne_velo_aprem=8.0 + i,
            moyenne_velo_soir=12.0 + i,
        )
        for i in range(7)
    ]
