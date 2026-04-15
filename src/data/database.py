from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

from config import settings


class Base(DeclarativeBase):
    pass


class Station(Base):
    __tablename__ = "stations"

    station_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    lat: Mapped[float] = mapped_column(Float)
    lon: Mapped[float] = mapped_column(Float)
    capacity: Mapped[int] = mapped_column(Integer, default=0)

    statuses: Mapped[list["StationStatusHistory"]] = relationship(back_populates="station")


class StationStatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    station_id: Mapped[str] = mapped_column(ForeignKey("stations.station_id"), index=True)
    collected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True)
    num_bikes_available: Mapped[int] = mapped_column(Integer, default=0)
    num_docks_available: Mapped[int] = mapped_column(Integer, default=0)
    num_ebikes_available: Mapped[int] = mapped_column(Integer, default=0)
    mechanical_bikes: Mapped[int] = mapped_column(Integer, default=0)

    station: Mapped[Station] = relationship(back_populates="statuses")


class WeatherHistory(Base):
    __tablename__ = "weather_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    temperature_c: Mapped[float] = mapped_column(Float)
    precipitation_mm: Mapped[float] = mapped_column(Float)
    wind_speed_kmh: Mapped[float] = mapped_column(Float)


Index("ix_status_station_time", StationStatusHistory.station_id, StationStatusHistory.collected_at)

engine = create_engine(settings.postgres_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def create_all() -> None:
    Base.metadata.create_all(bind=engine)
