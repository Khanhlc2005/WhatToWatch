import json

import pytest
from fastapi.testclient import TestClient
from requests import ConnectionError

from app.llm_client import OllamaClient
from app.main import app

client = TestClient(app)


def test_chat_uses_sample_context_and_returns_structured_answer(monkeypatch) -> None:
    def fake_generate(self, prompt: str, system_prompt: str | None = None, response_format=None) -> str:
        assert "tmdb:157336" in prompt
        assert "Chỉ dùng dữ liệu" in system_prompt
        assert response_format["type"] == "object"
        return json.dumps({
            "status": "answered", "answer": "Một lựa chọn về du hành không gian.",
            "movies": [{"movie_id": "tmdb:157336", "title": "Interstellar", "reason": "Science Fiction"}],
        })

    monkeypatch.setattr(OllamaClient, "generate", fake_generate)
    response = client.post("/internal/chat", json={"message": "Gợi ý phim du hành không gian"})
    assert response.status_code == 200
    assert response.json()["movies"][0]["title"] == "Interstellar"
    assert "Interstellar" in response.json()["reply"]


def test_explicit_empty_context_needs_no_model(monkeypatch) -> None:
    monkeypatch.setattr(OllamaClient, "generate", lambda *args, **kwargs: pytest.fail("Ollama called"))
    response = client.post("/internal/chat", json={"message": "Gợi ý phim", "movie_context": []})
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_context"


def test_context_without_movie_facts_returns_insufficient(monkeypatch) -> None:
    monkeypatch.setattr(OllamaClient, "generate", lambda *args, **kwargs: pytest.fail("Ollama called"))
    response = client.post("/internal/chat", json={
        "message": "Ai đạo diễn phim này?",
        "movie_context": [{"movie_id": "custom:1", "title": "Unknown Film"}],
    })
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_context"


def test_duplicate_context_ids_return_422() -> None:
    movie = {"movie_id": "custom:1", "title": "Same Film", "overview": "Some story."}
    response = client.post("/internal/chat", json={
        "message": "Gợi ý phim", "movie_context": [movie, movie],
    })
    assert response.status_code == 422


def test_supplied_context_is_used_instead_of_sample(monkeypatch) -> None:
    def fake_generate(self, prompt: str, system_prompt: str | None = None, response_format=None) -> str:
        assert "custom:1" in prompt
        assert "tmdb:157336" not in prompt
        return json.dumps({
            "status": "answered", "answer": "Một phim phù hợp trong ngữ cảnh.",
            "movies": [{"movie_id": "custom:1", "title": "Moon Film", "reason": "Science Fiction"}],
        })

    monkeypatch.setattr(OllamaClient, "generate", fake_generate)
    response = client.post("/internal/chat", json={
        "message": "Gợi ý phim khoa học viễn tưởng",
        "movie_context": [{
            "movie_id": "custom:1", "title": "Moon Film", "genres": ["Science Fiction"],
            "overview": "A journey to the Moon.",
        }],
    })
    assert response.status_code == 200
    assert response.json()["movies"][0]["movie_id"] == "custom:1"


def test_unparseable_model_reply_is_a_gateway_error(monkeypatch) -> None:
    monkeypatch.setattr(OllamaClient, "generate", lambda *args, **kwargs: "not-json")
    response = client.post("/internal/chat", json={"message": "Gợi ý phim"})
    assert response.status_code == 502


def test_ollama_connection_failure_is_service_unavailable(monkeypatch) -> None:
    def unavailable(*args, **kwargs):
        raise ConnectionError("offline")
    monkeypatch.setattr(OllamaClient, "generate", unavailable)
    response = client.post("/internal/chat", json={"message": "Gợi ý phim"})
    assert response.status_code == 503
