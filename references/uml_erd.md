# Diagramme logique simplifié

```text
stations (station_id PK)
  ├── name
  ├── lat
  ├── lon
  └── capacity
       |
       | 1 - n
       v
status_history (id PK)
  ├── station_id FK -> stations.station_id
  ├── collected_at
  ├── num_bikes_available
  ├── num_docks_available
  ├── num_ebikes_available
  └── mechanical_bikes

weather_history (id PK)
  ├── observed_at
  ├── temperature_c
  ├── precipitation_mm
  └── wind_speed_kmh
```
