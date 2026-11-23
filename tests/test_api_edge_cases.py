"""Extra request cases found while checking the complete app."""

import pytest

from app import create_app


@pytest.fixture
def client(sample_index):
    app = create_app(sample_index)
    app.testing = True
    return app.test_client()


@pytest.mark.parametrize("intent", [[], {}, ["route"]])
def test_invalid_pending_intent_does_not_crash(client, intent):
    response = client.post("/api/ask", json={
        "text": "where is the union", "pending": {"intent": intent, "missing": ["origin"]}
    })
    assert response.status_code == 200
    assert response.get_json()["slots"]["building"]["code"] == "0155"


@pytest.mark.parametrize("filename", ["app.js", "schedule.js", "schedule-model.js",
                                     "schedule-storage.js", "map-navigation.js",
                                     "saved-places.js", "saved-places-model.js", "saved-places-storage.js"])
def test_browser_modules_are_served_as_javascript(client, filename):
    response = client.get(f"/{filename}")
    assert response.status_code == 200
    assert "javascript" in response.content_type
