from fastapi.testclient import TestClient
from api.app.main import app


def test_health_returns_200_with_ok_status():
    """AC-1: GET /health returns 200 and {"status": "ok"}"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
