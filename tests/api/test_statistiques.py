from fastapi import status


class TestStatsGlobal:
    def test_returns_200(self, client):
        response = client.get("/v1/statistiques/global")
        assert response.status_code == status.HTTP_200_OK

    def test_structure(self, client):
        data = client.get("/v1/statistiques/global").json()
        expected_keys = [
            "nb_stations_total", "nb_stations_actives", "nb_velos_disponibles",
            "nb_places_libres", "taux_disponibilite", "derniere_maj",
        ]
        for key in expected_keys:
            assert key in data

    def test_taux_between_0_and_1(self, client):
        data = client.get("/v1/statistiques/global").json()
        assert 0 <= data["taux_disponibilite"] <= 1


class TestStatsSemaine:
    def test_returns_200(self, client):
        response = client.get("/v1/statistiques/station/1057387136/semaine")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_7_days(self, client):
        data = client.get("/v1/statistiques/station/1057387136/semaine").json()
        assert len(data) == 7

    def test_each_day_structure(self, client):
        data = client.get("/v1/statistiques/station/1057387136/semaine").json()
        for entry in data:
            for key in ["jour", "moyenne_velo_matin", "moyenne_velo_aprem", "moyenne_velo_soir"]:
                assert key in entry

    def test_unknown_station(self, client):
        response = client.get("/v1/statistiques/station/1/semaine")
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestStatsAuth:
    def test_global_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/statistiques/global")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_semaine_requires_auth(self, unauthenticated_client):
        response = unauthenticated_client.get("/v1/statistiques/station/1057387136/semaine")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
