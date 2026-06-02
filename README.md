
# 🚲  Analyse des données Vélib' — Projet BDE velib Liora

## 📌  Contexte du projet



Ce projet est une solution MLOps complète pour l'analyse et la prédiction de la disponibilité des vélos en libre-service Vélib' à Paris. Il s'appuie sur une architecture containeurisée incluant une API FastAPI, des modèles de Machine Learning, et un pipeline de données automatisé.

🎓 Ce projet a été réalisé dans le cadre du cursus **Data Engineer de LIORA / École des Mines Paris **.


---

## 🎯  Objectifs

Les principaux objectifs du projet sont :

- Nettoyer et structurer les données provenant de l'API Vélib' et d'autres sources
- Réaliser une analyse exploratoire des données (EDA)
- Identifier les tendances temporelles et géographiques
- Visualiser l'activité du réseau Vélib'
- Mettre en place des indicateurs de performance
- Tester des approches de prédiction (disponibilité, saturation, etc.)

---

## 🗂️ Structure du projet

```bash
mar26_bde_velib/
├── analytics # TO CHECK
├── docker # Configuration docker et script d'initialisation
│   └── stack
│       ├── init-mongo
│       ├── init-postgres
│       └── python
├── logs
├── models
│   └── figures
├── src # Scripts Python
│   ├── api # Configuration FastAPI
│   │   ├── core
│   │   ├── routers
│   │   ├── schemas
│   │   └── services
│   ├── config
│   ├── data  # Script d'intération au BDD
│   ├── features
│   ├── ml
│   ├── models #Scrrpt d'entrainement et interrogation du modèle de prédiction
│   ├── streamlit # Configuration Streamlit
│   └── visualization
└── tests # Tests unitaires
    └── api
├── LICENSE
├── README.md
├── requirements.txt # Dépendances Python
└── .gitignore
```
---

## 📊  Données utilisées

Les données proviennent de l'API Open Data Vélib\' Métropole, d'Openweathermap et de la SNCF / RATP.

### Sources possibles

- Disponibilité des stations
- Nombre de vélos mécaniques / électriques
- Capacité des stations
- Coordonnées GPS
- Historique temporel
- Météo en temps réel
- Perturbation et passage des métros/RER
---

## 🛠️ Technologies utilisées

### Langages & outils

- Python
- Git / GitHub
- PostgreSQL
- MongoDB
- RandomForest
- Docker
- FastAPI
- Streamlit

### Librairies principales

- pandas
- numpy
- matplotlib
- seaborn
- plotly
- scikit-learn
- requests

---

## ⚙️ Installation
### Prérequis

- Docker & Docker Compose
- Git

### 1. Création des répertoires
```bash
sudo mkdir -p /opt/docker/stack/init-postgres
sudo mkdir -p /opt/docker/stack/init-mongo
sudo mkdir -p /opt/docker/stack/python
sudo mkdir -p /opt/docker/stack/python/workspace
cd /opt/docker/stack
```

### 2. Cloner le repository
```bash
git clone https://github.com/DataScientest-Studio/mar26_bde_velib.git python/workspace
```

### 3. Copier les éléments nécessaires pour Docker
```bash
sudo cp -r /opt/docker/stack/python/workspace/docker/stack/. .
sudo chmod +x init-postgres/01-create-users.sh
```

### 4. Création du fichier .env
```bash
sudo nano .env
```
```bash
# PostgreSQL
POSTGRES_ADMIN_PASSWORD=MotDePasseAdminPG
PG_ROMAIN_PASSWORD=MotDePasseRomain
PG_NAHED_PASSWORD=MotDePasseNahed
PG_BELKACEM_PASSWORD=MotDePasseBelkacem
PG_VELIB_PASSWORD=MotDePasseVelib

# MongoDB
MONGO_ADMIN_PASSWORD=MotDePasseAdminMongo
MG_ROMAIN_PASSWORD=MotDePasseRomain
MG_NAHED_PASSWORD=MotDePasseNahed
MG_BELKACEM_PASSWORD=MotDePasseBelkacem
MG_VELIB_PASSWORD=MotDePasseVelib
```
```bash
sudo cat /opt/docker/stack/python/workspace/.env | sudo tee -a .env > /dev/null
```

### 5. Construire les images Docker
```bash
docker compose build --no-cache
```

### 6. Démarrer les containeurs Docker
```bash
docker compose up -d
```

### 7. Tester les containeurs Docker

```bash
sudo docker ps
```

---

## ▶️ Tester les services

### PostgreSQL (depuis le containeur Python)
*Pensez à remplacer le mot de passe par celui inséré.*
```bash
sudo docker exec -it python python -c "
import psycopg2
conn = psycopg2.connect(host='postgresql', dbname='db_romain', user='romain', password='MotDePasseRomain')
print('PostgreSQL OK')
conn.close()
"
```
### MongoDB (depuis le containeur Python)
*Pensez à remplacer le mot de passe par celui inséré.*
```bash
sudo docker exec -it python python -c "
from pymongo import MongoClient
client = MongoClient('mongodb://romain:MotDePasseRomain@mongodb:27017/db_romain')
print('MongoDB OK')
client.close()
"
```
### API
```bash
curl -i http://localhost:8000/health
```
### Streamlit
```bash
curl -i http://localhost:8501/
```
---

## 📈 Exemples d'analyses

- Répartition des stations par arrondissement.
- Taux d'occupation moyen.
- Disponibilité selon l'heure de la journée.
- Heatmap géographique des stations.
- Évolution du nombre de vélos disponibles.
- Comparaison vélos électriques vs mécaniques.

---

## 🧠  Pistes d'amélioration

- Analyse temps réel.
- Détection des stations critiques.
- Prévision de saturation des stations.

---

## 👥 Équipe projet & Contexte Académique

Projet réalisé par les membres du groupe BDE LIORA.

| Nom | Rôle | LinkedIn |
| :--- | :--- | :--- |
| Nahed KHEDHIRI | Data Engineering | [![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5.svg?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/nahed-khedhiri/) |
| Romain DELAUNAY | Data Engineering | [![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5.svg?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/rdelaunay/) |
| Belkacem TILMATINE | Data Engineering | [![LinkedIn](https://img.shields.io/badge/LinkedIn-%230077B5.svg?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/belkacem-tilmatine/) |


| | |
|---|---|
| 🎓 **Formation** | Data Engineer |
| 🏫 **Établissement** | LIORA / École des Mines Paris |
| 📅 **Promotion** | Mars 2026 |



---


## 📚  Ressources utiles

- [API Vélib' Métropole](https://www.velib-metropole.fr/donnees-open-data-gbfs-du-service-velib-metropole)
- [PRIM iles de france](https://prim.iledefrance-mobilites.fr/)
- [Meteo](https://openweathermap.org/api/current?collection=current_forecast)

---

## 📄 Licence

Projet pédagogique réalisé dans le cadre de la formation Data Engineer de LIORA / École des Mines Paris ❤️.

---

## ⭐ Contributions

Les contributions sont les bienvenues.

1. Fork du projet
2. Création d'une branche
3. Commit des modifications
4. Push de la branche
5. Ouverture d'une Pull Request
