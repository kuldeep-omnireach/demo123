from fastapi.testclient import TestClient
from src.main import app


def test_read_main():
    client = TestClient(app)
    response = client.get("/hello")
    assert response.status_code == 200
    assert response.json() == {"msg": "Hello World"}
