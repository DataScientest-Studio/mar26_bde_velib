"""
Faux prédicteur utilisé en CI ou en dev quand le modèle n'est pas dispo.
Reproduit la signature publique de Prediction.
"""
from datetime import date as date_type
import random


class FakePredictor:
    """Implémentation de secours : renvoie des prédictions déterministes."""

    def __init__(self):
        random.seed(42)  # reproductibilité

    def prediction_station(self, idstation, heures: list[str], date: str) -> list[dict]:
        if isinstance(idstation, int):
            idstation = [idstation]

        results = []
        for sid in idstation:
            for heure in heures:
                # Pseudo-prédiction stable : fonction de l'id + heure
                hour_int = int(heure.split(":")[0])
                pred = (int(sid) * 3 + hour_int * 2) % 25
                results.append({
                    "id_station": int(sid),
                    "heure": heure,
                    "date": date,
                    "prediction_nb_velo": int(pred),
                })
        return results

    def prediction_metro(self, id_arret_transport, nom_arret_transport,
                         heures: list[str], date: str) -> list[dict]:
        # 2 stations factices proches du métro
        fake_station_ids = [11218807773, 11218807774]
        return self.prediction_station(fake_station_ids, heures, date)
