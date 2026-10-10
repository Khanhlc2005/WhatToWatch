from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient, models

from app.main import app
from app.services import preference, recommendation

URL = '/internal/recommendations'


def vector(x, y=0):
    return [x, y] + [0.0] * 1022


@pytest.fixture
def api(monkeypatch):
    client = QdrantClient(':memory:')
    for name in ('movies', 'user_profiles'):
        client.create_collection(name, vectors_config={
            'dense': models.VectorParams(size=1024, distance=models.Distance.COSINE)
        })
    client.upsert('user_profiles', [models.PointStruct(
        id=7, vector={'dense': vector(1)},
        payload={'user_id': 7, 'profile_version': preference.PROFILE_VERSION}
    )])
    client.upsert('movies', [models.PointStruct(
        id=i, vector={'dense': vec}, payload={'movie_id': movie_id, 'genres': ['Drama'],
            'country': ['US'], 'language': 'en', 'year': 2000, 'rating': 8, 'runtime': 100}
    ) for i, movie_id, vec in [
        (1, 101, vector(1)), (2, 102, vector(.8, .6)),
        (3, 103, vector(0, 1)), (4, 104, vector(-1)),
        (5, 101, vector(.6, .8)), (6, None, vector(1)),
    ]])
    monkeypatch.setattr(recommendation, 'get_qdrant_client', lambda: client)
    monkeypatch.setattr(preference, 'get_qdrant_client', lambda: client)
    with TestClient(app) as http:
        yield http, client
    client.close()


def test_cosine_ranking_dedup_and_signed_scores(api):
    response = api[0].post(URL, json={'user_id': 7})
    assert response.status_code == 200
    assert response.json()['status'] == 'ready'
    hits = response.json()['hits']
    assert [h['movie_id'] for h in hits] == [101, 102, 103, 104]
    assert [h['score'] for h in hits] == pytest.approx([1, .8, 0, -1])


def test_filters_and_exclusions(api):
    response = api[0].post(URL, json={'user_id': 7, 'limit': 2, 'exclude_movie_ids': [101, 101],
        'filters': {'genres': ['Drama'], 'countries': ['US'], 'languages': ['en'],
            'year_min': 2000, 'year_max': 2000, 'rating_min': 8, 'runtime_max': 100}})
    assert [h['movie_id'] for h in response.json()['hits']] == [102, 103]


@pytest.mark.parametrize('filters', [
    {'genres': ['Comedy']}, {'exclude_genres': ['Drama']}, {'countries': ['FR']},
    {'languages': ['fr']}, {'year_min': 2001}, {'year_max': 1999},
    {'rating_min': 9}, {'runtime_max': 99},
])
def test_filters_never_relaxed(api, filters):
    response = api[0].post(URL, json={'user_id': 7, 'filters': filters})
    assert response.json() == {'user_id': 7, 'status': 'ready', 'hits': []}


def test_missing_profile_does_not_query_movies(api, monkeypatch):
    monkeypatch.setattr(api[1], 'query_points', lambda **kw: pytest.fail('unexpected retrieval'))
    assert api[0].post(URL, json={'user_id': 8}).json() == {
        'user_id': 8, 'status': 'cold_start', 'hits': []}


@pytest.mark.parametrize('payload', [
    {'user_id': 8, 'profile_version': 'ratings-v1'},
    {'user_id': True, 'profile_version': 'ratings-v1'},
    {'user_id': 7, 'profile_version': 'old'}, {},
])
def test_invalid_profile_metadata(api, payload):
    api[1].overwrite_payload('user_profiles', payload, points=[7])
    assert api[0].post(URL, json={'user_id': 7}).status_code == 503


def test_zero_profile_is_error(api):
    api[1].update_vectors('user_profiles', [models.PointVectors(id=7, vector={'dense': vector(0)})])
    assert api[0].post(URL, json={'user_id': 7}).status_code == 503


def test_invalid_candidates_and_ties(api, monkeypatch):
    ids = [None, True, '10', -1, 0, 2**63, 30, 20, 20, 40]
    scores = [1] * 8 + [.5, float('nan')]
    points = [SimpleNamespace(payload={'movie_id': mid}, score=score)
              for mid, score in zip(ids, scores)]
    monkeypatch.setattr(api[1], 'query_points', lambda **kw: SimpleNamespace(points=points))
    assert api[0].post(URL, json={'user_id': 7}).json()['hits'] == [
        {'movie_id': 20, 'score': 1}, {'movie_id': 30, 'score': 1}]


@pytest.mark.parametrize('body', [
    {}, {'user_id': 0}, {'user_id': True}, {'user_id': '7'}, {'user_id': 2**63},
    {'user_id': 7, 'limit': 0}, {'user_id': 7, 'limit': 101}, {'user_id': 7, 'limit': True},
    {'user_id': 7, 'exclude_movie_ids': [None]}, {'user_id': 7, 'exclude_movie_ids': ['101']},
    {'user_id': 7, 'filters': {'exclude_watched': True}}, {'user_id': 7, 'unexpected': 1},
])
def test_validation(api, body):
    assert api[0].post(URL, json=body).status_code == 422


@pytest.mark.parametrize('method', ['retrieve', 'query_points'])
def test_storage_errors(api, monkeypatch, method):
    def fail(**kwargs):
        raise RuntimeError('sensitive storage details')
    monkeypatch.setattr(api[1], method, fail)
    response = api[0].post(URL, json={'user_id': 7})
    assert response.status_code == 503
    assert 'sensitive' not in response.text


def test_snapshot_to_recommendation_update_and_delete(api):
    http, client = api
    # Remove duplicate catalog mapping before building profile.
    client.delete('movies', models.PointIdsList(points=[5]))
    snapshot = {'user_id': 8, 'ratings': [
        {'movie_id': 101, 'rating': 5}, {'movie_id': 102, 'rating': 4},
        {'movie_id': 103, 'rating': 1}]}
    assert http.put('/internal/preferences/snapshot', json=snapshot).json()['status'] == 'ready'
    first = http.post(URL, json={'user_id': 8}).json()['hits']
    snapshot['ratings'][0]['rating'] = 1
    snapshot['ratings'][2]['rating'] = 5
    assert http.put('/internal/preferences/snapshot', json=snapshot).status_code == 200
    second = http.post(URL, json={'user_id': 8}).json()['hits']
    assert first[0]['movie_id'] != second[0]['movie_id']
    http.put('/internal/preferences/snapshot', json={'user_id': 8, 'ratings': []})
    assert http.post(URL, json={'user_id': 8}).json()['status'] == 'cold_start'
