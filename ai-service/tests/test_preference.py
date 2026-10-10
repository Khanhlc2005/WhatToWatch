import math

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from app.main import app
from app.services import preference

URL = "/internal/preferences/snapshot"


def body(scores=(5, 4, 1), user_id=7):
    return {"user_id": user_id, "ratings": [
        {"movie_id": index + 101, "rating": score} for index, score in enumerate(scores)
    ]}


def basis(index):
    return [float(i == index) for i in range(1024)]


@pytest.fixture
def api(monkeypatch):
    client = QdrantClient(":memory:")
    for name in ("movies", "user_profiles"):
        client.create_collection(name, vectors_config={
            "dense": models.VectorParams(size=1024, distance=models.Distance.COSINE)
        })
    client.upsert("movies", points=[models.PointStruct(
        id=i + 1, vector={"dense": basis(i)}, payload={"movie_id": i + 101}
    ) for i in range(3)])
    monkeypatch.setattr(preference, "get_qdrant_client", lambda: client)
    with TestClient(app) as http:
        yield http, client
    client.close()


def profile(client, user_id=7):
    return client.retrieve("user_profiles", [user_id], with_vectors=True)


def test_formula():
    assert [preference.rating_weight(r) for r in (1, 2, 3, 4, 5)] == [-0.35, -0.175, 0, 0.5, 1]


@pytest.mark.parametrize("vector", [[], [0.0] * 1024, [float('nan')] * 1024,
                                    [float('inf')] * 1024, [True] * 1024])
def test_invalid_vectors(vector):
    assert preference.normalize(vector) is None


def test_snapshot_updates_replays_and_delete(api):
    http, client = api
    response = http.put(URL, json=body())
    assert response.status_code == 200
    assert response.json()['status'] == 'ready'
    assert response.json()['usable_rating_count'] == 3
    first = profile(client)[0]
    assert first.payload['user_id'] == 7
    assert first.payload['profile_version'] == 'ratings-v1'
    norm = math.sqrt(1 + .5**2 + .35**2)
    assert first.vector['dense'][:3] == pytest.approx([1/norm, .5/norm, -.35/norm])
    replay = body()
    replay['ratings'].reverse()
    assert http.put(URL, json=replay).status_code == 200
    assert profile(client)[0].vector == first.vector
    assert http.put(URL, json=body((1, 4, 5))).status_code == 200
    assert profile(client)[0].vector['dense'][0] < 0
    assert http.put(URL, json=body((5, 4))).json()['reason'] == 'insufficient_ratings'
    assert profile(client) == []


@pytest.mark.parametrize('scores', [(), (5,), (5, 4), (3, 3, 3)])
def test_cold_start(api, scores):
    response = api[0].put(URL, json=body(scores)).json()
    assert response['status'] == 'cold_start'
    assert response['reason'] == 'insufficient_ratings'
    assert profile(api[1]) == []


def test_missing_and_ambiguous_embeddings(api):
    http, client = api
    client.delete('movies', models.PointIdsList(points=[3]))
    client.upsert('movies', [models.PointStruct(id=4, vector={'dense': basis(0)}, payload={'movie_id': 101})])
    response = http.put(URL, json=body()).json()
    assert response['usable_rating_count'] == 1
    assert response['skipped_movies'] == [
        {'movie_id': 101, 'reason': 'ambiguous_movie_id'},
        {'movie_id': 103, 'reason': 'missing_embedding'},
    ]


def test_zero_sum_removes_old_profile(api):
    http, client = api
    http.put(URL, json=body())
    # Exact cancellation across three non-neutral signals.
    for i in range(3):
        client.update_vectors('movies', [models.PointVectors(id=i+1, vector={'dense': basis(0)})])
    response = http.put(URL, json=body((3.7, 2, 2))).json()
    assert response['usable_rating_count'] == 3
    assert response['reason'] == 'zero_vector'
    assert profile(client) == []


def test_user_isolation(api):
    http, client = api
    http.put(URL, json=body())
    http.put(URL, json=body(user_id=8))
    http.put(URL, json=body((), user_id=7))
    assert profile(client, 7) == []
    assert len(profile(client, 8)) == 1


@pytest.mark.parametrize('payload', [
    {}, {'user_id': True, 'ratings': []}, {'user_id': '7', 'ratings': []},
    {'user_id': 0, 'ratings': []}, {'user_id': 2**63, 'ratings': []},
    {'user_id': 7, 'ratings': [{'movie_id': 101, 'rating': 6}]},
    {'user_id': 7, 'ratings': [{'movie_id': 101, 'rating': True}]},
    {'user_id': 7, 'ratings': [{'movie_id': 101, 'rating': '5'}]},
    {'user_id': 7, 'ratings': [{'movie_id': 101, 'rating': 5}] * 2},
    {'user_id': 7, 'ratings': [], 'partial': True},
])
def test_invalid_snapshot(api, payload):
    assert api[0].put(URL, json=payload).status_code == 422


def test_read_failure_preserves_profile(api, monkeypatch):
    http, client = api
    http.put(URL, json=body())
    before = profile(client)[0]
    def fail(**kwargs):
        raise RuntimeError('sensitive connection details')
    monkeypatch.setattr(client, 'scroll', fail)
    response = http.put(URL, json=body((1, 4, 5)))
    assert response.status_code == 503
    assert 'sensitive' not in response.text
    assert profile(client)[0] == before


@pytest.mark.parametrize('method,scores', [('upsert', (5, 4, 1)), ('delete', ())])
def test_write_failure_returns_503(api, monkeypatch, method, scores):
    def fail(**kwargs):
        raise RuntimeError('sensitive storage failure')
    monkeypatch.setattr(api[1], method, fail)
    response = api[0].put(URL, json=body(scores))
    assert response.status_code == 503
    assert 'sensitive' not in response.text


def test_invalid_stored_embedding_is_reported(api):
    http, client = api
    client.update_vectors('movies', [models.PointVectors(id=3, vector={'dense': [0.0] * 1024})])
    response = http.put(URL, json=body()).json()
    assert response['status'] == 'cold_start'
    assert response['usable_rating_count'] == 2
    assert response['skipped_movies'] == [{'movie_id': 103, 'reason': 'invalid_embedding'}]
    assert profile(client) == []
