from fastapi import APIRouter, Depends
from src.api.schemas.statistiques import StatsGlobal, StatsJour
from src.api.services import statistiques_service
from src.api.dependencies import get_current_user

router = APIRouter(
    prefix="/v1/statistiques",
    tags=["Statistiques"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/global",
    response_model=StatsGlobal,
    summary="Statistiques globales du réseau Vélib'",
    description=(
        "Retourne une **vue d'ensemble** du réseau Vélib' à l'instant T :\n\n"
        "- **nb_stations_total** : nombre total de stations recensées\n"
        "- **nb_stations_actives** : stations effectivement opérationnelles\n"
        "- **nb_velos_disponibles** : total des vélos disponibles sur le réseau\n"
        "- **nb_places_libres** : total des places libres\n"
        "- **taux_disponibilite** : ratio vélos / capacité totale (entre 0 et 1)\n"
        "- **derniere_maj** : horodatage de la dernière agrégation\n\n"
        "### Cas d'usage\n\n"
        "- Tableaux de bord temps réel\n"
        "- Monitoring de la santé du réseau\n"
        "- Alertes (ex: taux < 10%)\n\n"
        "💡 **Performance** : cet endpoint agrège toutes les stations. Un cache de 30s à 1 min "
        "côté serveur (Redis) est fortement recommandé en production."
    )
)
def stats_global():
    return statistiques_service.get_stats_global()


@router.get(
    "/station/{id_station}/semaine",
    response_model=list[StatsJour],
    summary="Tendance hebdomadaire d'une station (7 jours)",
    description=(
        "Retourne les **statistiques journalières** d'une station sur les **7 derniers jours**.\n\n"
        "### Découpage horaire\n\n"
        "Chaque journée est découpée en 3 plages avec la moyenne des vélos disponibles :\n\n"
        "| Plage | Horaires |\n"
        "|---|---|\n"
        "| **moyenne_velo_matin** | 06h00 - 12h00 |\n"
        "| **moyenne_velo_aprem** | 12h00 - 18h00 |\n"
        "| **moyenne_velo_soir** | 18h00 - 00h00 |\n\n"
        "### Réponse\n\n"
        "Liste de 7 entrées (du plus ancien au plus récent), une par jour.\n\n"
        "### Cas d'usage\n\n"
        "- Identifier les heures de pointe / creuses d'une station\n"
        "- Détecter des anomalies (station vide en permanence)\n"
        "- Recommandations utilisateurs (\"partez plutôt à 07h45 que 08h30\")"
    ),
    responses={
        404: {"description": "Station introuvable"},
        422: {"description": "ID de station invalide"},
    },
)
def stats_semaine(id_station: int):
    return statistiques_service.get_stats_semaine(id_station)
