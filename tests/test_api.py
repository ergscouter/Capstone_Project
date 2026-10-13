import pytest

from app import create_app


@pytest.fixture
def client(sample_index):
    app = create_app(sample_index)
    app.testing = True
    return app.test_client()


def test_health_reports_building_count(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "buildings_loaded": 5}


def test_list_buildings(client):
    response = client.get("/api/buildings")
    assert response.status_code == 200
    assert len(response.get_json()) == 5


def test_get_building_by_code(client):
    response = client.get("/api/buildings/0155")
    assert response.status_code == 200
    assert response.get_json()["name"] == "Student Union"


def test_unknown_building_returns_404(client):
    assert client.get("/api/buildings/9999").status_code == 404


def test_search_endpoint(client):
    response = client.get("/api/search?q=science")
    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_search_rejects_overlong_query(client):
    response = client.get("/api/search?q=" + "a" * 101)
    assert response.status_code == 400


def test_home_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Campus Buddy" in response.data
