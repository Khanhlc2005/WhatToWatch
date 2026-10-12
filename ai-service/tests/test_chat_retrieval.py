"""Exercise the production chat path through retrieval, catalog, and generation."""

import json

import pytest
import requests
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from app.api.routers import chat as chat_router
from app.llm_client import OllamaClient
from app.main import app
from app.schemas.retrieval import MovieSearchHit, MovieSearchResponse
from app.services import context_builder, retrieval


def _response(status: int, body: dict) -> requests.Response:
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(body).encode("utf-8")
    response.url = "http://backend/movie-recommendation/movies/42"
    return response


@pytest.fixture
def catalog_chat(monkeypatch):
    qdrant = QdrantClient(":memory:")
    qdrant.create_collection(
        "movies",
        vectors_config={"dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)},
        sparse_vectors_config={"sparse": models.SparseVectorParams()},
    )
    qdrant.upsert("movies", points=[models.PointStruct(
        id=42,
        vector={"dense": [1.0] + [0.0] * 1023,
                "sparse": models.SparseVector(indices=[42], values=[1.0])},
        payload={"movie_id": 42, "imdb_id": "tt0000042", "tmdb_id": 4242,
                 "title": "Catalog Film", "genres": ["Science Fiction"],
                 "year": 2019, "country": ["US"], "language": "en", "rating": 8.0,
                 "runtime": 120},
    )])
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: qdrant)
    monkeypatch.setattr(retrieval, "embed_query", lambda _: {
        "dense": [1.0] + [0.0] * 1023, "sparse": {"42": 1.0},
    })
    with TestClient(app) as http:
        yield http
    qdrant.close()


def test_chat_uses_retrieved_mysql_movie_and_canonical_id(catalog_chat, monkeypatch):
    detail_calls = []

    def get_detail(url, timeout):
        detail_calls.append((url, timeout))
        return _response(200, {"code": 1000, "result": {
            "id": 42, "imdbId": "tt0000042", "tmdbId": 4242,
            "title": "Catalog Film", "overview": "A crew journeys across distant galaxies.",
            "releaseDate": "2019-01-01", "runtimeMinutes": 120,
            "crew": [{"name": "Jane Director", "job": "Director"}],
        }})

    def generate(self, prompt, system_prompt=None, response_format=None):
        assert '"movie_id": "42"' in prompt
        assert "A crew journeys across distant galaxies" in prompt
        assert "Jane Director" in prompt
        assert "tmdb:157336" not in prompt
        assert response_format["type"] == "object"
        return json.dumps({
            "status": "answered", "answer": "A film about a space journey.",
            "movies": [{"movie_id": "42", "title": "Catalog Film", "reason": "Science Fiction"}],
        })

    monkeypatch.setattr(context_builder.requests, "get", get_detail)
    monkeypatch.setattr(OllamaClient, "generate", generate)
    response = catalog_chat.post("/internal/chat", json={"message": "Suggest a space film"})

    assert response.status_code == 200
    assert response.json()["movies"][0]["movie_id"] == "42"
    assert response.json()["movies"][0]["reason"] == "Thể loại: Science Fiction"
    assert detail_calls[0][0].endswith("/movies/42")


def test_chat_applies_explicit_filters_and_handles_no_results(catalog_chat, monkeypatch):
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Ollama called"))
    monkeypatch.setattr(context_builder.requests, "get", lambda *_, **__: pytest.fail("Catalog called"))
    response = catalog_chat.post("/internal/chat", json={
        "message": "Suggest a film", "filters": {"year_min": 2025},
    })
    assert response.status_code == 200
    assert response.json()["status"] == "no_match"
    assert response.json()["movies"] == []


def test_chat_reports_catalog_outage_without_using_fixture(catalog_chat, monkeypatch):
    def unavailable(*_, **__):
        raise requests.ConnectionError("backend offline")

    monkeypatch.setattr(context_builder.requests, "get", unavailable)
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Ollama called"))
    response = catalog_chat.post("/internal/chat", json={"message": "Suggest a film"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Movie catalog is unavailable"


def test_chat_reports_retrieval_outage_without_using_fixture(monkeypatch):
    def unavailable(*_):
        raise RuntimeError("Qdrant offline")

    monkeypatch.setattr(chat_router, "search_movies", unavailable)
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Ollama called"))
    with TestClient(app) as http:
        response = http.post("/internal/chat", json={"message": "Suggest a film"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Movie retrieval is unavailable"


def test_context_builder_rejects_mismatched_catalog_identity(catalog_chat, monkeypatch):
    monkeypatch.setattr(context_builder.requests, "get", lambda *_, **__: _response(200, {
        "code": 1000, "result": {"id": 42, "imdbId": "tt9999999", "title": "Wrong Film"},
    }))
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Ollama called"))
    response = catalog_chat.post("/internal/chat", json={"message": "Suggest a film"})
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_context"


def test_missing_mysql_movie_is_skipped(catalog_chat, monkeypatch):
    monkeypatch.setattr(context_builder.requests, "get", lambda *_, **__: _response(400, {
        "code": 2001, "message": "Movie not found",
    }))
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Ollama called"))
    response = catalog_chat.post("/internal/chat", json={"message": "Suggest a film"})
    assert response.status_code == 200
    assert response.json()["status"] == "insufficient_context"


def test_context_builder_fills_five_movies_in_retrieval_order(monkeypatch):
    def hit(movie_id):
        return MovieSearchHit(
            point_id=str(movie_id), movie_id=movie_id, imdb_id=None, tmdb_id=None,
            title=f"Film {movie_id}" if movie_id else None, score=1.0,
            id_status="present_unverified" if movie_id else "missing",
        )

    calls = []

    def fetch(movie_id):
        calls.append(movie_id)
        if movie_id == 2:
            return None
        return {"id": movie_id, "title": f"Film {movie_id}", "overview": "A catalog movie."}

    monkeypatch.setattr(context_builder, "fetch_movie_detail", fetch)
    search = MovieSearchResponse(
        collection="movies", mode="hybrid",
        hits=[hit(None), hit(1), hit(2), hit(1), *(hit(i) for i in range(3, 9))],
    )
    context = context_builder.build_movie_context(search)
    assert [movie.movie_id for movie in context] == ["1", "3", "4", "5", "6"]
    assert calls == [1, 2, 3, 4, 5, 6]


def test_actor_filter_checks_full_catalog_cast(monkeypatch):
    monkeypatch.setattr(context_builder, "fetch_movie_detail", lambda movie_id: {
        "id": movie_id, "title": "Ensemble Film", "overview": "An ensemble story.",
        "cast": [{"name": f"Actor {index}"} for index in range(10)] + [{"name": "Target Actor"}],
    })
    search = MovieSearchResponse(collection="movies", mode="hybrid", hits=[MovieSearchHit(
        point_id="1", movie_id=1, imdb_id=None, tmdb_id=None, title="Ensemble Film",
        score=1.0, id_status="present_unverified",
    )])
    context = context_builder.build_movie_context(search, actor="Target Actor")
    assert [movie.movie_id for movie in context] == ["1"]


def test_follow_up_rehydrates_previous_recommendation(catalog_chat, monkeypatch):
    def get_detail(url, timeout):
        movie_id = int(url.rsplit("/", 1)[-1])
        return _response(200, {"code": 1000, "result": {
            "id": movie_id, "title": "Previous Film" if movie_id == 43 else "Catalog Film",
            "overview": "A journey through space.", "releaseDate": "2020-01-01",
        }})

    monkeypatch.setattr(context_builder.requests, "get", get_detail)
    monkeypatch.setattr(OllamaClient, "generate", lambda *_, **__: pytest.fail("Model called for catalog fact"))
    response = catalog_chat.post("/internal/chat", json={
        "message": "Phim đó phát hành năm nào?",
        "history": [
            {"role": "user", "content": "Gợi ý phim không gian"},
            {"role": "assistant", "content": "Previous Film", "movie_ids": [43]},
        ],
    })
    assert response.status_code == 200
    assert response.json()["movies"][0]["movie_id"] == "43"
    assert "2020" in response.json()["answer"]
    assert response.json()["tool_name"] == "movie_detail"
