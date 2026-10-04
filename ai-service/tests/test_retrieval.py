import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from app.main import app
from app.services import retrieval


@pytest.fixture
def search(monkeypatch):
    client = QdrantClient(":memory:")
    client.create_collection("movies", vectors_config={
        "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)
    }, sparse_vectors_config={"sparse": models.SparseVectorParams()})
    base = {"genres": ["Drama"], "country": ["US"], "language": "en",
            "year": 2000, "rating": 8.5, "runtime": 110}
    client.upsert("movies", points=[models.PointStruct(
        id=i, vector={"dense": [1.0] + [0.0] * 1023,
                      "sparse": models.SparseVector(indices=[42], values=[float(i)])},
        payload={**base, "title": f"Fixture {i}", "imdb_id": f"tt{i:07d}", "tmdb_id": i,
                 "movie_id": None if i == 1 else i, "genres": ["Horror"] if i == 3 else ["Drama"]}
    ) for i in (1, 2, 3)])
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: client)
    monkeypatch.setattr(retrieval, "embed_query", lambda _: {
        "dense": [1.0] + [0.0] * 1023, "sparse": {"42": 1.0}
    })
    with TestClient(app) as http:
        yield http, client
    client.close()


@pytest.mark.parametrize("mode", ["dense", "sparse"])
def test_both_modes_apply_all_filters_and_report_missing_ids(search, mode):
    http, _ = search
    response = http.post("/internal/qdrant/search", json={"query": "drama", "mode": mode,
        "filters": {"genres": ["Drama"], "exclude_genres": ["Horror"], "countries": ["US"],
                    "languages": ["en"], "year_min": 2000, "year_max": 2000,
                    "runtime_max": 110, "rating_min": 8.5}})
    assert response.status_code == 200
    hits = response.json()["hits"]
    assert {hit["point_id"] for hit in hits} == {"1", "2"}
    assert next(hit for hit in hits if hit["point_id"] == "1")["movie_id"] is None
    assert next(hit for hit in hits if hit["point_id"] == "1")["id_status"] == "missing"
    assert next(hit for hit in hits if hit["point_id"] == "2")["id_status"] == "present_unverified"
    if mode == "sparse":
        assert hits[0]["point_id"] == "2"


@pytest.mark.parametrize("filters", [
    {"year_min": 2001}, {"year_max": 1999}, {"runtime_max": 109}, {"rating_min": 9},
    {"countries": ["FR"]}, {"languages": ["fr"]}, {"genres": ["Comedy"]},
    {"exclude_genres": ["Drama", "Horror"]},
])
@pytest.mark.parametrize("mode", ["dense", "sparse"])
def test_filters_never_relax_to_fill_results(search, filters, mode):
    response = search[0].post("/internal/qdrant/search", json={"query": "film", "mode": mode, "filters": filters})
    assert response.status_code == 200
    assert response.json()["hits"] == []


@pytest.mark.parametrize("body", [
    {"query": " "}, {"query": "film", "limit": 0}, {"query": "film", "limit": 101},
    {"query": "film", "mode": "hybrid"}, {"query": "film", "filters": {"director": "Someone"}},
    {"query": "film", "filters": {"year_min": 2020, "year_max": 2000}},
    {"query": "film", "filters": {"genres": [" "]}},
])
def test_invalid_inputs(search, body):
    assert search[0].post("/internal/qdrant/search", json=body).status_code == 422


def test_empty_sparse_does_not_call_qdrant(search, monkeypatch):
    monkeypatch.setattr(retrieval, "embed_query", lambda _: {"sparse": {}})
    monkeypatch.setattr(retrieval, "get_qdrant_client", lambda: pytest.fail("No Qdrant call expected"))
    response = search[0].post("/internal/qdrant/search", json={"query": "film", "mode": "sparse"})
    assert response.status_code == 200
    assert response.json()["hits"] == []


def test_failure_is_503_without_internal_details(search, monkeypatch):
    def fail(_):
        raise RuntimeError("internal sensitive connection details")
    monkeypatch.setattr(retrieval, "embed_query", fail)
    response = search[0].post("/internal/qdrant/search", json={"query": "film"})
    assert response.status_code == 503
    assert "sensitive" not in response.text


@pytest.mark.parametrize('movie_id,status', [('7', 'invalid'), (True, 'invalid'), (-1, 'invalid'), (None, 'missing')])
def test_never_substitutes_point_id_for_invalid_movie_id(search, movie_id, status):
    http, client = search
    client.set_payload('movies', {'movie_id': movie_id}, points=[3])
    hit = http.post('/internal/qdrant/search', json={'query': 'film', 'mode': 'sparse', 'limit': 1}).json()['hits'][0]
    assert hit['point_id'] == '3'
    assert hit['movie_id'] is None
    assert hit['id_status'] == status


def test_deduplicates_mysql_ids_without_reordering_scores(search):
    http, client = search
    client.set_payload('movies', {'movie_id': 2}, points=[3])
    hits = http.post('/internal/qdrant/search', json={'query': 'film', 'mode': 'sparse'}).json()['hits']
    assert [hit['point_id'] for hit in hits] == ['3', '1']


def test_invalid_dense_vector_is_rejected(search, monkeypatch):
    monkeypatch.setattr(retrieval, 'embed_query', lambda _: {'dense': [0.0] * 1024})
    assert search[0].post('/internal/qdrant/search', json={'query': 'film'}).status_code == 503
