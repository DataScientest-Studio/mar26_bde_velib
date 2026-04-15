# Projet Vélib' — Data Engineer

Ce dépôt complète le starter `mar26_bde_velib` pour répondre au besoin métier principal : **prédire la disponibilité des stations à +2h et exposer ces résultats via une API et un dashboard**.

## Besoin métier couvert

Le backlog et les supports projet convergent sur quatre attentes fortes :

1. **Collecter et historiser** les flux Vélib (`station_information` et `station_status`) toutes les 5 minutes.
2. **Structurer la donnée** dans une base SQL avec historique par station, plus un stockage NoSQL pour les événements non structurés.
3. **Prédire le nombre de vélos disponibles à +2h** avec un modèle Random Forest v1.
4. **Exposer ces résultats** dans une API FastAPI, un dashboard Streamlit et un pipeline batch orchestrable.

## Fonctionnalités implémentées

- client de collecte Vélib avec retry, timeout et snapshots JSON horodatés ;
- client météo réutilisable ;
- génération d'un dataset analytique parquet ;
- feature engineering pour le modèle de prédiction ;
- entraînement d'un Random Forest avec split temporel ;
- script d'inférence réutilisable par l'API ;
- calcul des KPIs du dashboard (`network_availability_rate`, stations critiques) ;
- API FastAPI avec `/health`, `/predict` et `/stats` ;
- application Streamlit de démonstration ;
- DAG Airflow de collecte → dataset → entraînement ;
- `docker-compose.yml` avec PostgreSQL, MongoDB, API et Streamlit ;
- tests unitaires de base pour l'API.

## Structure principale

```text
src/
├── airflow/velib_batch_pipeline.py
├── api/main.py
├── collecte/
│   ├── velib_client.py
│   └── weather_client.py
├── data/
│   ├── database.py
│   └── make_dataset.py
├── features/build_features.py
├── ml/
│   ├── analytics.py
│   ├── predict.py
│   └── train_model.py
└── streamlit/app.py
```

## Lancement local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=src
pytest
uvicorn api.main:app --reload
```

## Enchaînement recommandé

```bash
python -c "from collecte.velib_client import collect_velib_snapshot; collect_velib_snapshot()"
python -c "from collecte.weather_client import fetch_weather_forecast, save_weather_snapshot; save_weather_snapshot(fetch_weather_forecast())"
python -c "from data.make_dataset import build_dataset; build_dataset()"
python -c "from ml.train_model import train_random_forest; train_random_forest()"
uvicorn api.main:app --reload
streamlit run src/streamlit/app.py
```

## Docker

```bash
docker compose up --build
```

## Livrables utiles

- `references/schema.sql` : base relationnelle PostgreSQL ;
- `references/uml_erd.md` : schéma logique ;
- `docker-compose.yml` : socle de déploiement ;
- `tests/test_api.py` : couverture de base des endpoints.
