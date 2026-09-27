from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_openapi_exposes_qdrant_and_chat_routes() -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/internal/qdrant/health" in paths
    assert "/internal/qdrant/sample" in paths
    assert "/internal/chat" in paths
