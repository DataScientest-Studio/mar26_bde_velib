import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.dependencies import get_current_user
from src.api.schemas.auth import User


def _fake_user():
    """Utilisateur factice pour bypasser l'auth dans les tests."""
    return User(username="test_user")


@pytest.fixture
def client():
    app.dependency_overrides[get_current_user] = _fake_user
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def unauthenticated_client():
    """Client sans override, pour tester que l'auth est bien active."""
    return TestClient(app)


