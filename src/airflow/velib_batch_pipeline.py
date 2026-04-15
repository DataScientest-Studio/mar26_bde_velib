from __future__ import annotations

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator

from collecte.velib_client import collect_velib_snapshot
from collecte.weather_client import fetch_weather_forecast, save_weather_snapshot
from data.make_dataset import build_dataset
from ml.train_model import train_random_forest


def collect_weather() -> None:
    payload = fetch_weather_forecast()
    save_weather_snapshot(payload)


def default_args() -> dict[str, object]:
    return {"owner": "velib", "retries": 3, "retry_delay": timedelta(minutes=5)}


with DAG(
    dag_id="velib_batch_pipeline",
    description="Collecte API Vélib + météo, construction dataset et entraînement modèle",
    start_date=datetime(2026, 4, 1),
    schedule="0 * * * *",
    catchup=False,
    default_args=default_args(),
    tags=["velib", "ml", "batch"],
) as dag:
    collect_velib = PythonOperator(task_id="collect_velib", python_callable=collect_velib_snapshot)
    collect_meteo = PythonOperator(task_id="collect_meteo", python_callable=collect_weather)
    make_dataset = PythonOperator(task_id="make_dataset", python_callable=build_dataset)
    train_model = PythonOperator(task_id="train_model", python_callable=train_random_forest)

    [collect_velib, collect_meteo] >> make_dataset >> train_model
