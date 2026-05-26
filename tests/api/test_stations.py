from fastapi import status

class TestAuthentication:
    def test_stations_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/stations")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_station_detail_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/stations/1")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_etat_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/stations/1/etat")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_etats_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/stations/etats")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

class TestListStations:
    def test_returns_200(self, client):
        response = client.get("/v1/stations")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_list(self, client):
        response = client.get("/v1/stations")
        assert isinstance(response.json(), list)

    def test_station_structure(self, client):
        response = client.get("/v1/stations")
        station = response.json()[0]
        expected_keys = {
            "id_station", "nom_station", "longitude", "latitude",
            "capacite_totale", "proximite",
        }
        assert expected_keys.issubset(station.keys())

    def test_proximite_structure(self, client):
        response = client.get("/v1/stations")
        station = response.json()[0]
        if station["proximite"]:
            prox = station["proximite"][0]
            assert "arret_transport" in prox
            assert "distance" in prox


class TestGetStation:
    def test_existing_station(self, client):
        response = client.get("/v1/stations/1057387136")
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["id_station"] == 1057387136

    def test_unknown_station_returns_404(self, client):
        response = client.get("/v1/stations/1")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_invalid_id_returns_422(self, client):
        # FastAPI valide automatiquement : "abc" n'est pas un int
        response = client.get("/v1/stations/abc")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestEtatStation:
    def test_returns_200(self, client):
        response = client.get("/v1/stations/1057387136/etat")
        assert response.status_code == status.HTTP_200_OK

    def test_structure(self, client):
        response = client.get("/v1/stations/1057387136/etat")
        data = response.json()
        expected_keys = {
            "id_station", "nb_velo", "nb_velo_classique", "nb_velo_electrique",
            "nb_place_libre", "capacite_totale", "derniere_maj", "meteo",
        }
        assert expected_keys.issubset(data.keys())

    def test_meteo_structure(self, client):
        response = client.get("/v1/stations/1057387136/etat")
        meteo = response.json()["meteo"]
        assert {"description", "temperature", "humidite", "vent"}.issubset(meteo.keys())

    def test_coherence_nb_velo(self, client):
        """nb_velo doit être égal à la somme classique + électrique."""
        response = client.get("/v1/stations/1057387136/etat")
        data = response.json()
        assert data["nb_velo"] == data["nb_velo_classique"] + data["nb_velo_electrique"]

    def test_coherence_places(self, client):
        """nb_velo + nb_place_libre = capacite_totale."""
        response = client.get("/v1/stations/1057387136/etat")
        data = response.json()
        assert data["nb_velo"] + data["nb_place_libre"] == data["capacite_totale"]

    def test_unknown_station_returns_404(self, client):
        response = client.get("/v1/stations/1/etat")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestListEtats:
    def test_returns_200(self, client):
        response = client.get("/v1/stations/etats")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_list(self, client):
        response = client.get("/v1/stations/etats")
        assert isinstance(response.json(), list)

    def test_each_etat_has_meteo(self, client):
        response = client.get("/v1/stations/etats")
        for etat in response.json():
            assert "meteo" in etat
            assert "description" in etat["meteo"]
