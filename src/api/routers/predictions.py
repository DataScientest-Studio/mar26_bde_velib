from datetime import date as date_type
from fastapi import APIRouter, Depends, Query
from src.api.schemas.predictions import PredictionStation, PredictionMetro, PredictionTrajet
from src.api.services import predictions_service
from src.api.dependencies import get_current_user,get_predictor
import re
from fastapi import HTTPException, status

router = APIRouter(
    prefix="/v1/predictions",
    tags=["Predictions"],
    dependencies=[Depends(get_current_user)],
)

HEURE_PATTERN = r"^\d{2}:\d{2}$"
HEURE_REGEX = re.compile(r"^\d{2}:\d{2}$")

def _validate_heures(heures: list[str]) -> None:
    for h in heures:
        if not HEURE_REGEX.match(h):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"Heure invalide : '{h}'. Format attendu : HH:mm",
            )

@router.get(
    "/station",
    response_model=PredictionStation,
    summary="Prédiction de disponibilité pour une station",
    description=(
        "Prédit le **nombre de vélos disponibles** dans une station à une ou plusieurs heures.\n\n"
        "### Paramètres\n\n"
        "- **id_station** : ID de la station\n"
        "- **heure** : une ou plusieurs heures au format **HH:mm**. "
        "Répétez le paramètre pour en passer plusieurs.\n"
        "- **date** *(optionnel)* : format **YYYY-MM-DD**. Défaut = aujourd'hui.\n\n"
        "### Exemples d'appel\n\n"
        "`GET /v1/predictions/station?id_station=42&heure=08:30`\n\n"
        "`GET /v1/predictions/station?id_station=42&heure=08:30&heure=12:00&heure=18:00`"
    ),
    responses={404: {"description": "Station introuvable"}},
)
def predict_station(
    id_station: int = Query(..., description="ID de la station"),
    heure: list[str] = Query(
        ...,
        description="Une ou plusieurs heures HH:mm (répéter le paramètre)",
        examples=["08:30", "12:00"],
    ),
    date: date_type | None = Query(None, description="Format YYYY-MM-DD"),
    predictor=Depends(get_predictor),
):
    _validate_heures(heure)
    return predictions_service.predict_station(predictor, id_station, heure, date)


@router.get(
    "/metro",
    response_model=PredictionMetro,
    summary="Prédiction autour d'un arrêt de transport",
    description=(
        "Prédictions pour les stations Vélib' proches d'un arrêt de transport, "
        "à une ou plusieurs heures.\n\n"
        "### Exemples d'appel\n\n"
        "`GET /v1/predictions/metro?arret_transport=République&heure=18:00`\n\n"
        "`GET /v1/predictions/metro?arret_transport=République&heure=08:00&heure=18:00`"
    ),
    responses={404: {"description": "Arrêt de transport introuvable"}},
)
def predict_metro(
    arret_transport: str = Query(..., examples="République"),
    heure: list[str] = Query(..., examples=["18:00"]),
    date: date_type | None = Query(None),
    predictor=Depends(get_predictor),
):
    _validate_heures(heure)
    return predictions_service.predict_metro(predictor, arret_transport, heure, date)


@router.get(
    "/trajet",
    response_model=PredictionTrajet,
    summary="Prédiction complète pour un trajet (départ + arrivée)",
    description=(
        "Prédit la disponibilité **au départ** (vélos) et **à l'arrivée** (places libres) "
        "pour un trajet complet, en calculant aussi l'**heure d'arrivée estimée**.\n\n"
        "### Deux modes d'utilisation\n\n"
        "**🗺️ Mode GPS** — fournir les coordonnées, l'API trouve les stations les plus proches :\n"
        "- `lat_depart`, `lon_depart`\n"
        "- `lat_arrivee`, `lon_arrivee`\n\n"
        "**🆔 Mode IDs** — fournir directement les identifiants de stations connus :\n"
        "- `id_station_depart`\n"
        "- `id_station_arrivee`\n\n"
        "**🔀 Mode mixte** — vous pouvez mélanger : GPS au départ, ID à l'arrivée "
        "(ou inversement).\n\n"
        "### Paramètres communs\n\n"
        "- **heure_depart** *(obligatoire)* : heure de départ au format **HH:mm**\n"
        "- **date** *(optionnel)* : date du trajet, défaut = aujourd'hui\n\n"
        "### Réponse\n\n"
        "- `station_depart` : station de départ + prédiction du nombre de vélos\n"
        "- `station_arrivee` : station d'arrivée + places libres actuelles et prédites\n"
        "- `heure_arrivee_estimee` : basée sur la distance et une vitesse moyenne de 15 km/h\n\n"
        "### Exemples d'appel\n\n"
        "**Mode GPS** : "
        "`GET /v1/predictions/trajet?lat_depart=48.86&lon_depart=2.35"
        "&lat_arrivee=48.87&lon_arrivee=2.37&heure_depart=08:00`\n\n"
        "**Mode IDs** : "
        "`GET /v1/predictions/trajet?id_station_depart=42&id_station_arrivee=88&heure_depart=08:00`"
    ),
    responses={
        400: {"description": "Combinaison de paramètres invalide (manque départ ou arrivée)"},
        404: {"description": "Aucune station trouvée à proximité des coordonnées fournies"},
    },
)
def predict_trajet(
    heure_depart: str = Query(..., pattern=HEURE_PATTERN),
    date: date_type | None = Query(None),
    # Option A : coordonnées
    lat_depart: float | None = Query(None),
    lon_depart: float | None = Query(None),
    lat_arrivee: float | None = Query(None),
    lon_arrivee: float | None = Query(None),
    # Option B : IDs
    id_station_depart: int | None = Query(None),
    id_station_arrivee: int | None = Query(None),
):
    return predictions_service.predict_trajet(
        heure_depart=heure_depart,
        date_=date,
        lat_depart=lat_depart,
        lon_depart=lon_depart,
        lat_arrivee=lat_arrivee,
        lon_arrivee=lon_arrivee,
        id_station_depart=id_station_depart,
        id_station_arrivee=id_station_arrivee,
    )
