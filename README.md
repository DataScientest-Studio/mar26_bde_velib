# 🚲  Analyse des données Vélib' — Projet BDE DataScientest

## 📌  Contexte du projet



Ce projet est une solution MLOps complète pour l'analyse et la prédiction de la disponibilité des vélos en libre-service Vélib' à Paris. Il s'appuie sur une architecture moderne incluant une API FastAPI, des modèles de Machine Learning, et un pipeline de données automatisé.

🎓 Ce projet a été réalisé dans le cadre du cursus **Data Enginee de LIORA / Paris NINE PLS**.


---

## 🎯  Objectifs

Les principaux objectifs du projet sont :

- Nettoyer et structurer les données Vélib'
- Réaliser une analyse exploratoire des données (EDA)
- Identifier les tendances temporelles et géographiques
- Visualiser l'activité du réseau Vélib'
- Mettre en place des indicateurs de performance
- Tester des approches de prédiction (disponibilité, saturation, etc.)

---

## 🗂️ Structure du projet

```bash
mar26_bde_velib/
│
├── data/                  # Script d'intération au BDD
├── notebooks/             # Notebooks d'analyse
├── src/                   # Scripts Python
├──── config                  #Script configuration des log 
├──── model                   #Scrpt d'entrainement et intérogation du model
├── visualizations/        # Graphiques et exports
├── models/                # Modèles ML éventuels
├── requirements.txt       # Dépendances Python
├── README.md
└── .gitignore
```

---

## 📊  Données utilisées

Les données proviennent de l'API Open Data Vélib' Métropole.

### Sources possibles

- Disponibilité des stations
- Nombre de vélos mécaniques / électriques
- Capacité des stations
- Coordonnées GPS
- Historique temporel

---

## 🛠️ Technologies utilisées

### Langages & outils

- Python
- Git / GitHub

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

- Python 3.9+
- Docker & Docker Compose
- Git

### 1. Cloner le repository

```bash
git clone https://github.com/DataScientest-Studio/mar26_bde_velib.git
cd mar26_bde_velib
```

### 2. Créer un environnement virtuel

```bash
python -m venv venv
```

### 3. Activer l'environnement

#### Linux / MacOS

```bash
source venv/bin/activate
```

#### Windows

```bash
venv\Scripts\activate
```

### 4. Installer les dépendances

```bash
pip install -r requirements.txt
```

---

## ▶️ Lancer le projet

### Démarrer Jupyter Notebook

```bash
jupyter notebook
```

Ou lancer directement un script Python :

```bash
python src/main.py
```

---

## 📈 Exemples d'analyses

- Répartition des stations par arrondissement
- Taux d'occupation moyen
- Disponibilité selon l'heure de la journée
- Heatmap géographique des stations
- Évolution du nombre de vélos disponibles
- Comparaison vélos électriques vs mécaniques

---

## 🧠  Pistes d'amélioration

- Analyse temps réel
- Détection des stations critiques
- Prévision de saturation des stations

---

## 👥 Équipe projet & Contexte Académique

Projet réalisé par les membres du groupe BDE LIORA.

| Nom | Rôle |
|------|------|
| Nahed KHEDHIRI | Data Engineering |
| Romain DELAUNAY | Data Engineering  |
| Belkacem TILMATINE | Data Engineering |


| | |
|---|---|
| 🎓 **Formation** | Data Engineer |
| 🏫 **Établissement** | LIORA / Paris NINE PLS |
| 📅 **Promotion** | Mars 2026 |



---


## 📚  Ressources utiles

- [API Vélib' Métropole](https://www.velib-metropole.fr/donnees-open-data-gbfs-du-service-velib-metropole)
- [PRIM iles de france](https://prim.iledefrance-mobilites.fr/)
- [Meteo](https://openweathermap.org/api/current?collection=current_forecast)

---

## 📄 Licence

Projet pédagogique réalisé dans le cadre de la formation .

---

## ⭐ Contributions

Les contributions sont les bienvenues.

1. Fork du projet
2. Création d'une branche
3. Commit des modifications
4. Push de la branche
5. Ouverture d'une Pull Request
