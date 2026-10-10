import sys
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'qdrant/scripts'))
import index_catalog as index


def movie():
    return dict(movie_id=3, imdb_id='tt123', tmdb_id=7, title='Test', release_date='2000-01-01',
                text_template_version='v1', embedding_text='Test')


class Client:
    def __init__(self, points):
        self.points = points

    def scroll(self, *args, **kwargs):
        return self.points, None


def point(m):
    return SimpleNamespace(id=index.common.point_id(m['imdb_id']), payload=index.common.make_payload(m),
                           vector={'dense': [1.0] * 1024, 'sparse': SimpleNamespace(indices=[1], values=[1.0])})


def test_resume_skips_verified_points():
    m = movie()
    assert index.pending_movies(Client([point(m)]), 'movies', [m]) == []
    assert index.pending_movies(Client([]), 'movies', [m]) == [m]


def test_refuses_conflicting_payload():
    m = movie()
    p = point(m)
    p.payload['movie_id'] = 99
    with pytest.raises(ValueError, match='conflicts'):
        index.pending_movies(Client([p]), 'movies', [m])


def test_refuses_orphan_and_invalid_vector():
    m = movie()
    p = point(m)
    with pytest.raises(ValueError, match='Unexpected'):
        index.pending_movies(Client([p]), 'movies', [])
    p.vector['dense'] = [0.0] * 1024
    with pytest.raises(ValueError, match='Invalid'):
        index.pending_movies(Client([p]), 'movies', [m])


def test_resume_with_real_qdrant_client():
    from qdrant_client import QdrantClient, models

    m = movie()
    p = point(m)
    with closing(QdrantClient(':memory:')) as client:
        index.common.ensure_collection(client, 1024)
        client.upsert(index.common.COLLECTION, points=[models.PointStruct(
            id=p.id, payload=p.payload,
            vector={'dense': [1.0] * 1024,
                    'sparse': models.SparseVector(indices=[1, 2], values=[0.5, 0.25])},
        )])
        assert index.pending_movies(client, index.common.COLLECTION, [m]) == []
        assert client.count(index.common.COLLECTION, exact=True).count == 1


def test_rejects_corrupt_sparse_vector():
    m = movie()
    p = point(m)
    p.vector['sparse'].values = [float('nan')]
    with pytest.raises(ValueError, match='Invalid'):
        index.pending_movies(Client([p]), 'movies', [m])


def test_memory_projection_preserves_payload_and_text(tmp_path):
    import json
    m = {**movie(), 'cast': [{'name': 'Actor'}], 'overview': 'Long metadata',
         'genres': [{'name': 'Drama'}], 'production_countries': [{'iso_3166_1': 'US'}]}
    path = tmp_path / 'movies.jsonl'
    path.write_text(json.dumps(m) + '\n')
    projected = index.load_index_movies(path)[0]
    assert 'cast' not in projected
    assert 'overview' not in projected
    assert projected['embedding_text'] == m['embedding_text']
    assert index.common.make_payload(projected) == index.common.make_payload(m)
