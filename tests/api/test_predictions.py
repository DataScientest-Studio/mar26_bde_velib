from fastapi import status


class TestPredictionStation:
    def test_returns_200(self, client):
        response = client.get(
            "/v1/predictions/station?id_station=1&heure=08:30&date=2025-01-15"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id_station"] == 1
        assert data["predictions"][0]["heure"] == "08:30"
        assert "prediction_nb_velo" in data["predictions"][0]

    def test_structure(self, client):
        response = client.get("/v1/predictions/station?id_station=1&heure=08:30")
        data = response.json()
        assert data["id_station"] == 1
        assert "date" in data
        assert isinstance(data["predictions"], list)
        assert data["predictions"][0]["heure"] == "08:30"
        assert isinstance(data["predictions"][0]["prediction_nb_velo"], int)

    def test_with_explicit_date(self, client):
        response = client.get(
            "/v1/predictions/station?id_station=1&heure=08:30&date=2025-01-15"
        )
        assert response.json()["date"] == "2025-01-15"

    '''def test_multiple_heures(self, client):
        response = client.get(
            "/v1/predictions/station?id_station=1&heure=08:30&heure=12:00&heure=18:00"
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["predictions"]) == 3'''

    def test_invalid_heure_format(self, client):
        response = client.get("/v1/predictions/station?id_station=1&heure=invalid")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_missing_required_param(self, client):
        response = client.get("/v1/predictions/station?id_station=1")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_unknown_station(self, client):
        response = client.get("/v1/predictions/station?id_station=99999&heure=08:30")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestPredictionMetro:
    def test_returns_200(self, client):
        response = client.get(
            "/v1/predictions/metro?arret_transport=République&heure=08:30"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "stations" in response.json()
        assert len(response.json()["stations"]) > 0

    def test_returns_list_of_stations(self, client):
        response = client.get(
            "/v1/predictions/metro?arret_transport=République&heure=08:30"
        )
        data = response.json()
        assert isinstance(data["stations"], list)
        assert len(data["stations"]) > 0

    def test_station_structure(self, client):
        response = client.get(
            "/v1/predictions/metro?arret_transport=République&heure=08:30"
        )
        station = response.json()["stations"][0]
        for key in ["id_station", "nom_station", "distance_metres", "predictions"]:
            assert key in station
        assert "heure" in station["predictions"][0]
        assert "prediction_nb_velo" in station["predictions"][0]

    '''def test_multiple_heures(self, client):
        response = client.get(
            "/v1/predictions/metro?arret_transport=République"
            "&heure=08:30&heure=18:00"
        )
        assert response.status_code == status.HTTP_200_OK
        station = response.json()["stations"][0]
        assert len(station["predictions"]) == 2'''


class TestPredictionsAuth:
    def test_station_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get(
            "/v1/predictions/station?id_station=1&heure=08:30"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_metro_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get(
            "/v1/predictions/metro?arret_transport=X&heure=08:30"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
