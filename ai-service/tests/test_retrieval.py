from types import SimpleNamespace

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


@pytest.mark.parametrize("mode", ["dense", "sparse", "hybrid"])
def test_all_modes_apply_all_filters_and_report_missing_ids(search, mode):
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
@pytest.mark.parametrize("mode", ["dense", "sparse", "hybrid"])
def test_filters_never_relax_to_fill_results(search, filters, mode):
    response = search[0].post("/internal/qdrant/search", json={"query": "film", "mode": mode, "filters": filters})
    assert response.status_code == 200
    assert response.json()["hits"] == []


@pytest.mark.parametrize("body", [
    {"query": " "}, {"query": "film", "limit": 0}, {"query": "film", "limit": 101},
    {"query": "film", "mode": "unknown"}, {"query": "film", "filters": {"director": "Someone"}},
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
@pytest.mark.parametrize('mode', ['sparse', 'hybrid'])
def test_never_substitutes_point_id_for_invalid_movie_id(search, movie_id, status, mode):
    http, client = search
    client.set_payload('movies', {'movie_id': movie_id}, points=[3])
    hits = http.post('/internal/qdrant/search', json={'query': 'film', 'mode': mode}).json()['hits']
    hit = next(hit for hit in hits if hit['point_id'] == '3')
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


def _point(point_id, movie_id, score, imdb_id=None):
    return SimpleNamespace(id=point_id, score=score, payload={
        'movie_id': movie_id, 'imdb_id': imdb_id, 'title': f'Fixture {point_id}', 'tmdb_id': None,
    })


def test_rrf_rewards_agreement_over_one_high_branch_score():
    dense = [_point(1, 1, 0.99), _point(2, 2, 0.50), _point(3, 3, 0.10)]
    sparse = [_point(3, 3, 100.0), _point(2, 2, 1.0)]
    hits = retrieval._fuse_rrf({'dense': dense, 'sparse': sparse}, limit=3)
    assert [point.id for point, _ in hits] == [3, 2, 1]
    assert hits[0][1] == pytest.approx(1 / (retrieval.RRF_K + 3) + 1 / (retrieval.RRF_K + 1))
    assert hits[1][1] == pytest.approx(2 / (retrieval.RRF_K + 2))


def test_rrf_deduplicates_movie_id_within_and_across_branches():
    dense = [_point(10, 7, 0.9), _point(11, 7, 0.8), _point(12, None, 0.7, 'tt12')]
    sparse = [_point(13, 7, 9.0), _point(14, None, 8.0, 'tt12')]
    hits = retrieval._fuse_rrf({'dense': dense, 'sparse': sparse}, limit=10)
    assert [point.id for point, _ in hits] == [10, 14]
    assert hits[0][1] == pytest.approx(2 / (retrieval.RRF_K + 1))
    assert hits[1][1] == pytest.approx(1 / (retrieval.RRF_K + 3) + 1 / (retrieval.RRF_K + 2))


def test_rrf_ties_are_deterministic():
    dense = [_point(2, 2, 0.5), _point(1, 1, 0.4)]
    sparse = [_point(1, 1, 10), _point(2, 2, 9)]
    assert [point.id for point, _ in retrieval._fuse_rrf(
        {'dense': dense, 'sparse': sparse}, limit=1
    )] == [2]


def test_hybrid_uses_both_queries_and_returns_fused_scores(search, monkeypatch):
    http, client = search
    calls = []
    original = client.query_points

    def record(**kwargs):
        calls.append(kwargs)
        return original(**kwargs)

    monkeypatch.setattr(client, 'query_points', record)
    response = http.post('/internal/qdrant/search', json={
        'query': 'film', 'mode': 'hybrid', 'limit': 2,
        'filters': {'genres': ['Drama']},
    })
    assert response.status_code == 200
    assert response.json()['mode'] == 'hybrid'
    assert len(response.json()['hits']) <= 2
    assert {call['using'] for call in calls} == {'dense', 'sparse'}
    assert all(call['limit'] == 2 and call['query_filter'] is not None for call in calls)
    assert all(hit['score'] < 1 for hit in response.json()['hits'])


def test_hybrid_empty_sparse_still_returns_dense_results(search, monkeypatch):
    monkeypatch.setattr(retrieval, 'embed_query', lambda _: {
        'dense': [1.0] + [0.0] * 1023, 'sparse': {},
    })
    response = search[0].post('/internal/qdrant/search', json={'query': 'film', 'mode': 'hybrid'})
    assert response.status_code == 200
    assert len(response.json()['hits']) == 3
    assert all(hit['score'] == pytest.approx(1 / (retrieval.RRF_K + rank))
               for rank, hit in enumerate(response.json()['hits'], start=1))


def test_hybrid_both_branches_empty(search, monkeypatch):
    monkeypatch.setattr(retrieval, 'embed_query', lambda _: {
        'dense': [1.0] + [0.0] * 1023, 'sparse': {},
    })
    response = search[0].post('/internal/qdrant/search', json={
        'query': 'film', 'mode': 'hybrid', 'filters': {'year_min': 2025},
    })
    assert response.status_code == 200
    assert response.json()['hits'] == []


def test_hybrid_qdrant_failure_returns_generic_503(search, monkeypatch):
    http, client = search
    original = client.query_points

    def fail_sparse(**kwargs):
        if kwargs['using'] == 'sparse':
            raise RuntimeError('internal sensitive connection details')
        return original(**kwargs)

    monkeypatch.setattr(client, 'query_points', fail_sparse)
    response = http.post('/internal/qdrant/search', json={'query': 'film', 'mode': 'hybrid'})
    assert response.status_code == 503
    assert 'sensitive' not in response.text
