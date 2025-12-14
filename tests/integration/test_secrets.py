from fastapi.testclient import TestClient
from artreactor.app import app

client = TestClient(app)


def test_set_secret():
    response = client.post(
        "/secrets/", json={"key": "api_key", "value": "12345", "scope": "USER"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
