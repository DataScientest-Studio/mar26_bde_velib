from fastapi import status


class TestPredictionStation:
    def test_returns_200(self, client):
        response = client.get("/v1/predictions/station?id_station=1&heure=08:30")
        assert response.status_code == status.HTTP_200_OK

    def test_structure(self, client):
        response = client.get("/v1/predictions/station?id_station=1&heure=08:30")
        data = response.json()
        assert data["id_station"] == 1
        assert data["heure"] == "08:30"
        assert "date" in data
        assert isinstance(data["prediction_nb_velo"], int)

    def test_with_explicit_date(self, client):
        response = client.get(
            "/v1/predictions/station?id_station=1&heure=08:30&date=2025-01-15"
        )
        assert response.json()["date"] == "2025-01-15"

    def test_invalid_heure_format(self, client):
        response = client.get("/v1/predictions/station?id_station=1&heure=8h30")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_required_param(self, client):
        response = client.get("/v1/predictions/station?id_station=1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unknown_station(self, client):
        response = client.get("/v1/predictions/station?id_station=99999&heure=08:30")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPredictionMetro:
    def test_returns_200(self, client):
        response = client.get("/v1/predictions/metro?arret_transport=République&heure=08:30")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_list_of_stations(self, client):
        response = client.get("/v1/predictions/metro?arret_transport=République&heure=08:30")
        data = response.json()
        assert "stations" in data
        assert isinstance(data["stations"], list)
        assert len(data["stations"]) > 0

    def test_station_structure(self, client):
        response = client.get("/v1/predictions/metro?arret_transport=République&heure=08:30")
        station = response.json()["stations"][0]
        for key in ["id_station", "nom_station", "distance_metres", "heure", "prediction_nb_velo"]:
            assert key in station


class TestPredictionTrajet:
    def test_with_station_ids(self, client):
        response = client.get(
            "/v1/predictions/trajet"
            "?id_station_depart=1&id_station_arrivee=2&heure_depart=08:30"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["station_depart"]["id_station"] == 1
        assert data["station_arrivee"]["id_station"] == 2

    def test_with_gps(self, client):
        response = client.get(
            "/v1/predictions/trajet"
            "?lat_depart=48.86&lon_depart=2.36"
            "&lat_arrivee=48.85&lon_arrivee=2.37"
            "&heure_depart=08:30"
        )
        assert response.status_code == status.HTTP_200_OK

    def test_missing_depart_info(self, client):
        response = client.get(
            "/v1/predictions/trajet?id_station_arrivee=2&heure_depart=08:30"
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_response_has_heure_arrivee(self, client):
        response = client.get(
            "/v1/predictions/trajet"
            "?id_station_depart=1&id_station_arrivee=2&heure_depart=08:30"
        )
        assert "heure_arrivee_estimee" in response.json()


class TestPredictionsAuth:
    def test_station_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/predictions/station?id_station=1&heure=08:30")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_metro_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/predictions/metro?arret_transport=X&heure=08:30")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_trajet_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get(
            "/v1/predictions/trajet?id_station_depart=1&id_station_arrivee=2&heure_depart=08:30"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
