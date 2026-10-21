from fastapi.testclient import TestClient
from api.app.main import app


def test_AC_1_1_health_endpoint():
    """AC-1.1: Given api.app.main defines app, GET /health returns 200 and {'status': 'ok'}"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
