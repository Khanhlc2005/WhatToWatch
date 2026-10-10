import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from map_mysql_ids import map_movies


def test_join_uses_identity_and_preserves_source():
    movies = [{'imdb_id': 'tt123', 'tmdb_id': 77, 'movie_id': None, 'title': 'Same title'},
              {'imdb_id': 'tt456', 'tmdb_id': 88, 'movie_id': None, 'title': 'Same title'}]
    rows = [{'id': '20', 'imdb_id': 'tt456', 'tmdb_id': '88'},
            {'id': '10', 'imdb_id': 'tt123', 'tmdb_id': '77'}]
    assert [m['movie_id'] for m in map_movies(movies, rows)] == [10, 20]
    assert all(m['movie_id'] is None for m in movies)


@pytest.mark.parametrize('rows', [
    [],
    [{'id': '1', 'imdb_id': 'tt123', 'tmdb_id': '99'}],
    [{'id': 'uuid', 'imdb_id': 'tt123', 'tmdb_id': '77'}],
    [{'id': '1', 'imdb_id': 'tt123', 'tmdb_id': '77'}, {'id': '1', 'imdb_id': 'tt456', 'tmdb_id': '88'}],
])
def test_rejects_unreliable_mapping(rows):
    with pytest.raises(ValueError):
        map_movies([{'imdb_id': 'tt123', 'tmdb_id': 77, 'movie_id': None}], rows)


def test_rejects_existing_id_conflict():
    with pytest.raises(ValueError):
        map_movies([{'imdb_id': 'tt123', 'tmdb_id': 77, 'movie_id': 2}],
                   [{'id': '1', 'imdb_id': 'tt123', 'tmdb_id': '77'}])
