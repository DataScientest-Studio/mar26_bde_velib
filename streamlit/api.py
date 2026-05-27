# api.py
from fastapi import FastAPI , APIRouter, Query, HTTPException
import uvicorn
from datetime import date, timedelta
import random
import math

app = FastAPI()

fake_db = [
    {"id": 1, "name": "Alice", "score": 95},
    {"id": 2, "name": "Bob", "score": 87},
]

stations_db = [
    { "id_station" :  501862076 , "nom_station" : "Place Nelson Mandela" , "longitude" : 2.1961666225454  ,"latitude" : 48.862453313908 , "capacite_totale" : 22 , "proximite" : [{ "arret_transport" : 2121 , "distance" : 11}] } ,
    
    { "id_station" :  19331959862 , "nom_station" : "Bas du Mont-Mesly" , "longitude" : 2.460837  ,"latitude" : 48.779751, "capacite_totale" : 27 , "proximite" : [{ "arret_transport" : 2121 , "distance" : 11}] } ,
    { "id_station" :  54000581 , "nom_station" : "Croulebarde - Corvisart" , "longitude" :  2.3481646925210953 ,"latitude" : 48.830981659316855 , "capacite_totale" : 34 , "proximite" : [{ "arret_transport" : 2121 , "distance" : 11}] } 
    
    ]

stations_etat_db = [
    { "id_station" :  501862076 , "nb_velo" : 10 , "nb_velo_classique" : 4 , "nb_velo_electrique" :6, "nb_place_libre" : 12 , "capacite_totale" : 22 , "derniere_maj" : "15-05-2026" , "meteo" : [{ "description" : "beau" , "temperature" : 16 , "humidite" : 30 ,"vent" : 5}] } ,
    
    { "id_station" :  19331959862 , "nb_velo" : 14 , "nb_velo_classique" : 8 , "nb_velo_electrique" :6, "nb_place_libre" : 13 , "capacite_totale" : 27 , "proximite" : [{ "arret_transport" : 2121 , "distance" : 11}] } ,
    { "id_station" :  54000581 , "nb_velo" : 30 , "nb_velo_classique" : 14 , "nb_velo_electrique" : 16, "nb_place_libre" : 4 , "capacite_totale" : 34 , "proximite" : [{ "arret_transport" : 2121 , "distance" : 11}] } 
    
    ]


METRO_STATIONS = {
    "chatelet": [
        {"id_station": 101, "nom_station": "Châtelet Nord",  "distance_metres": 120},
        {"id_station": 102, "nom_station": "Châtelet Sud",   "distance_metres": 250},
        {"id_station": 103, "nom_station": "Châtelet Est",   "distance_metres": 380},
    ],
    "republique": [
        {"id_station": 201, "nom_station": "République Place",    "distance_metres": 80},
        {"id_station": 202, "nom_station": "République Oberkampf", "distance_metres": 310},
        {"id_station": 203, "nom_station": "République Temple",    "distance_metres": 420},
    ],
    "bastille": [
        {"id_station": 301, "nom_station": "Bastille Arsenal",  "distance_metres": 150},
        {"id_station": 302, "nom_station": "Bastille Opéra",    "distance_metres": 290},
        {"id_station": 303, "nom_station": "Bastille Richard",  "distance_metres": 500},
    ],
    "nation": [
        {"id_station": 401, "nom_station": "Nation Picpus",    "distance_metres": 100},
        {"id_station": 402, "nom_station": "Nation Av. Maine", "distance_metres": 230},
        {"id_station": 403, "nom_station": "Nation Cours",     "distance_metres": 410},
    ],
}


def generate_semaine(id_station: int):
    today = date.today()
    result = []

    for i in range(6, -1, -1):
        jour = today - timedelta(days=i)
        result.append({
            "jour": jour.strftime("%Y-%m-%d"),
            "moyenne_velo_matin": random.randint(2, 10),
            "moyenne_velo_aprem": random.randint(1, 8),
            "moyenne_velo_soir":  random.randint(3, 12),
        })

    return result






def predict_velo(id_station: int, heure: str, jour: date) -> int:
    """
    Simulation d'une prédiction basée sur :
    - L'heure (heures de pointe = plus de vélos utilisés)
    - Le jour de la semaine (semaine vs weekend)
    - L'id_station (seed pour varier par station)
    """
    try:
        h, m = map(int, heure.split(":"))
    except ValueError:
        raise HTTPException(status_code=422, detail="Format heure invalide, attendu HH:mm")

    heure_decimal = h + m / 60

    # ── Courbe de fréquentation (sin) ─────────────────────────────
    # Pic matin ~8h, pic soir ~18h
    matin = math.exp(-((heure_decimal - 8) ** 2) / 4)
    soir  = math.exp(-((heure_decimal - 18) ** 2) / 4)
    courbe = (matin + soir) * 10

    # ── Bonus weekend (moins de vélos dispo) ──────────────────────
    est_weekend = jour.weekday() >= 5
    bonus_weekend = 1.3 if est_weekend else 1.0

    # ── Seed par station pour varier les résultats ────────────────
    random.seed(id_station + h + jour.toordinal())
    bruit = random.uniform(0.8, 1.2)

    prediction = int(courbe * bonus_weekend * bruit)
    prediction = max(0, min(prediction, 20))  # clamp entre 0 et 20

    return prediction



@app.get("/users")
def get_users():
    return fake_db


@app.get("/v1/stations")
def get_stations():
    return stations_db 

@app.get("/v1/stations/{user_id}")
def get_stations(user_id: int):
    
    return next((u for u in stations_db if u["id_station"] == user_id), None)


@app.get("/v1/stations/{user_id}/etat")
def get_stations(user_id: int):
    
    return next((u for u in stations_etat_db if u["id_station"] == user_id), None)


@app.get("/v1/statistiques/station/{id}/semaine")
def get_semaine(id: int):
    return generate_semaine(id)


@app.get("/v1/predictions/station")
def get_prediction(
    id_station: int       = Query(..., description="ID de la station"),
    heure: list[str]      = Query(..., description="Liste d'heures au format HH:mm"),
    date_param: str       = Query(None, alias="date", description="Date au format YYYY-MM-DD"),
):
    # ── Date (défaut aujourd'hui) ──────────────────────────────────
    if date_param:
        try:
            jour = date.fromisoformat(date_param)
        except ValueError:
            raise HTTPException(status_code=422, detail="Format date invalide, attendu YYYY-MM-DD")
    else:
        jour = date.today()

    # ── Prédiction pour chaque heure ──────────────────────────────
    predictions = [
        {
            "heure": h,
            "prediction_nb_velo": predict_velo(id_station, h, jour),
        }
        for h in heure
    ]

    return {
        "id_station":  id_station,
        "date":        jour.strftime("%Y-%m-%d"),
        "predictions": predictions,
    }



@app.get("/v1/predictions/metro")
def get_prediction_metro(
    arret_transport: str = Query(..., description="ID ou nom de l'arrêt métro"),
    heure: str           = Query(..., description="Heure au format HH:mm"),
    date_param: str      = Query(None, alias="date", description="Date au format YYYY-MM-DD"),
    ):

    print(f"get arret  {arret_transport}")
    # ── Date (défaut aujourd'hui) ──────────────────────────────────
    if date_param:
        try:
            jour = date.fromisoformat(date_param)
        except ValueError:
            raise HTTPException(status_code=422, detail="Format date invalide, attendu YYYY-MM-DD")
    else:
        jour = date.today()

    # ── Recherche de l'arrêt (par nom ou id) ──────────────────────
    arret_key = arret_transport.lower().strip()
    stations_proches = METRO_STATIONS.get(arret_key)

    if not stations_proches:
        # Recherche partielle si nom exact pas trouvé
        for key in METRO_STATIONS:
            if arret_key in key or key in arret_key:
                stations_proches = METRO_STATIONS[key]
                break

    if not stations_proches:
        raise HTTPException(
            status_code=404,
            detail=f"Arrêt '{arret_transport}' introuvable. Arrêts disponibles : {list(METRO_STATIONS.keys())}"
        )

    # ── Prédiction pour chaque station proche ─────────────────────
    result = []
    for s in stations_proches:
        result.append({
            "id_station":         s["id_station"],
            "nom_station":        s["nom_station"],
            "distance_metres":    s["distance_metres"],
            "heure":              heure,
            "prediction_nb_velo": predict_velo(s["id_station"], heure, jour),
        })

    # ── Tri par distance ───────────────────────────────────────────
    result.sort(key=lambda x: x["distance_metres"])

    return {"arret_transport": arret_transport, "date": jour.strftime("%Y-%m-%d"), "stations": result}




@app.get("/users/{user_id}")
def get_user(user_id: int):
    return next((u for u in fake_db if u["id"] == user_id), None)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
