import csv
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import NAMESPACE_URL, uuid5

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'qdrant/scripts'))
from sync_movie_ids import expected_ids, scan, sync


def point(movie_id=None, tmdb_id=7):
    return SimpleNamespace(id=str(uuid5(NAMESPACE_URL, 'whattowatch:movie:tt123')),
                           payload={'imdb_id': 'tt123', 'tmdb_id': tmdb_id, 'movie_id': movie_id})


class Client:
    def __init__(self, points):
        self.points = points
        self.snapshots = 0
        self.updates = 0

    def scroll(self, *args, **kwargs):
        assert kwargs['with_vectors'] is False
        return self.points, None

    def create_snapshot(self, *args, **kwargs):
        self.snapshots += 1
        return SimpleNamespace(name='backup.snapshot')

    def batch_update_points(self, collection, update_operations, wait):
        assert wait is True
        self.updates += 1
        for op in update_operations:
            for item in self.points:
                if str(item.id) == str(op.set_payload.points[0]):
                    item.payload.update(op.set_payload.payload)


def test_sync_snapshots_before_payload_only_write_and_reruns_safely():
    client = Client([point()])
    assert sync(client, 'movies', {'tt123': (10, 7)})['to_update'] == 1
    assert (client.snapshots, client.updates) == (0, 0)
    result = sync(client, 'movies', {'tt123': (10, 7)}, apply=True)
    assert (result['updated'], result['failed'], result['snapshot']) == (1, 0, 'backup.snapshot')
    assert client.points[0].payload['movie_id'] == 10
    assert sync(client, 'movies', {'tt123': (10, 7)}, apply=True)['to_update'] == 0
    assert (client.snapshots, client.updates) == (1, 1)


def test_conflicting_identity_refuses_writes():
    client = Client([point(tmdb_id=8)])
    with pytest.raises(ValueError, match='conflicts'):
        sync(client, 'movies', {'tt123': (10, 7)}, apply=True)
    assert (client.snapshots, client.updates) == (0, 0)


def test_processed_and_csv_must_match(tmp_path):
    mapping = tmp_path / 'mapping.csv'
    with mapping.open('w', newline='') as target:
        writer = csv.DictWriter(target, fieldnames=['id', 'imdb_id', 'tmdb_id'])
        writer.writeheader()
        writer.writerow({'id': '10', 'imdb_id': 'tt123', 'tmdb_id': '7'})
    movies = tmp_path / 'movies.jsonl'
    movies.write_text(json.dumps({'movie_id': 10, 'imdb_id': 'tt123', 'tmdb_id': 7}) + '\n')
    assert expected_ids(mapping, movies) == {'tt123': (10, 7)}
    movies.write_text(json.dumps({'movie_id': 11, 'imdb_id': 'tt123', 'tmdb_id': 7}) + '\n')
    with pytest.raises(ValueError, match='conflicts'):
        expected_ids(mapping, movies)
