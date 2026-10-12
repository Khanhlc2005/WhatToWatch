from fastapi.testclient import TestClient

from app.api.routers import chat as chat_router
from app.main import app
from app.schemas.rag import MovieContext
from app.schemas.retrieval import MovieSearchResponse
from app.services import chat_tools


def test_natural_filters_reach_retrieval_as_valid_json(monkeypatch) -> None:
    captured = []

    def search(request):
        captured.append(request)
        return MovieSearchResponse(collection="movies", mode="hybrid", hits=[])

    monkeypatch.setattr(chat_router, "search_movies", search)
    monkeypatch.setattr(chat_router, "build_movie_context", lambda search, director=None, actor=None: [])
    with TestClient(app) as http:
        response = http.post("/internal/chat", json={
            "message": "Gợi ý phim kinh dị từ năm 2010 đến 2020 điểm IMDb trên 7",
        })
    assert response.status_code == 200
    assert captured[0].filters.model_dump(exclude_defaults=True) == {
        "genres": ["Horror"], "year_min": 2010, "year_max": 2020, "rating_min": 7.0,
    }
    assert captured[0].mode == "hybrid"
    assert captured[0].rerank is True
    assert captured[0].candidate_k == 20
    assert response.json()["applied_filters"]["retrieval"]["genres"] == ["Horror"]


def test_filter_endpoint_works_without_retrieval_or_ollama(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "search_movies", lambda _: (_ for _ in ()).throw(AssertionError("retrieval called")))
    with TestClient(app) as http:
        response = http.post("/internal/chat/filters", json={
            "message": "Gợi ý phim hành động nhưng tránh phim kinh dị sau năm 2015",
        })
    assert response.status_code == 200
    assert response.json()["retrieval"]["genres"] == ["Action"]
    assert response.json()["retrieval"]["exclude_genres"] == ["Horror"]
    assert response.json()["retrieval"]["year_min"] == 2016


def test_invalid_natural_filter_fails_before_retrieval(monkeypatch) -> None:
    monkeypatch.setattr(chat_router, "search_movies", lambda _: (_ for _ in ()).throw(AssertionError("retrieval called")))
    with TestClient(app) as http:
        response = http.post("/internal/chat", json={"message": "Phim từ năm 2020 đến 2010"})
    assert response.status_code == 422


def test_comparison_calls_catalog_tool_and_uses_only_catalog_facts(monkeypatch) -> None:
    movies = [
        MovieContext(movie_id="1", title="Film One", year=2010, runtime_minutes=100),
        MovieContext(movie_id="2", title="Film Two", year=2020, runtime_minutes=120),
    ]
    calls = []

    def detail(ids):
        calls.append(ids)
        return movies

    monkeypatch.setattr(chat_tools, "build_context_for_movie_ids", detail)
    with TestClient(app) as http:
        response = http.post("/internal/chat", json={
            "message": "So sánh Film One và Film Two",
            "movie_context": [movie.model_dump() for movie in movies],
        })
    assert response.status_code == 200
    assert calls == [[1, 2]]
    assert response.json()["tool_name"] == "compare_movies"
    assert "2010" in response.json()["answer"] and "2020" in response.json()["answer"]
