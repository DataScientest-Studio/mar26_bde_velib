CREATE TABLE IF NOT EXISTS stations (
    station_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    capacity INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS status_history (
    id BIGSERIAL PRIMARY KEY,
    station_id VARCHAR(64) NOT NULL REFERENCES stations(station_id),
    collected_at TIMESTAMPTZ NOT NULL,
    num_bikes_available INTEGER NOT NULL DEFAULT 0,
    num_docks_available INTEGER NOT NULL DEFAULT 0,
    num_ebikes_available INTEGER NOT NULL DEFAULT 0,
    mechanical_bikes INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_status_station_time ON status_history(station_id, collected_at DESC);

CREATE TABLE IF NOT EXISTS weather_history (
    id BIGSERIAL PRIMARY KEY,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature_c DOUBLE PRECISION NOT NULL,
    precipitation_mm DOUBLE PRECISION NOT NULL,
    wind_speed_kmh DOUBLE PRECISION NOT NULL
);
