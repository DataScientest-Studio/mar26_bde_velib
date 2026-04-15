from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    velib_base_url: str = Field(
        default="https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole"
    )
    weather_api_url: str = Field(default="https://api.open-meteo.com/v1/forecast")
    collection_interval_minutes: int = Field(default=5)

    data_dir: Path = Field(default=Path("data"))
    raw_dir: Path = Field(default=Path("data/raw"))
    processed_dir: Path = Field(default=Path("data/processed"))
    model_dir: Path = Field(default=Path("models"))

    postgres_url: str = Field(default="sqlite:///data/velib.db")
    mongo_url: str = Field(default="mongodb://localhost:27017/")
    mongo_database: str = Field(default="velib")

    default_latitude: float = Field(default=48.8566)
    default_longitude: float = Field(default=2.3522)
    alert_threshold_bikes: int = Field(default=2)
    alert_threshold_docks: int = Field(default=2)

    def ensure_directories(self) -> None:
        for path in (self.data_dir, self.raw_dir, self.processed_dir, self.model_dir):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
