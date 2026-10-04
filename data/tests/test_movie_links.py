import importlib.util
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

spec = importlib.util.spec_from_file_location("movie_links", Path(__file__).parents[1] / "scripts/validate_movie_links.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fixture():
    movie = {"movie_id": 7, "imdb_id": "tt0000001", "tmdb_id": 9}
    row = {"id": "7", "imdb_id": "tt0000001", "tmdb_id": "9"}
    point = {"id": str(uuid5(NAMESPACE_URL, "whattowatch:movie:tt0000001")), "payload": dict(movie)}
    return movie, row, point


def test_complete_matching_export():
    movie, row, point = fixture()
    assert module.audit_links([movie], [row], [point])["status"] == "PASS"


def test_missing_sources_never_pass():
    movie, _, _ = fixture()
    report = module.audit_links([movie])
    assert report["status"] == "INCOMPLETE"
    assert len(report["not_run"]) == 2


def test_duplicates_mismatches_and_missing_points():
    movie, row, point = fixture()
    point["payload"]["movie_id"] = 10
    point["id"] = "wrong"
    report = module.audit_links([movie, dict(movie, imdb_id="tt0000002")], [row, row], [point])
    codes = {issue["code"] for issue in report["issues"]}
    assert {"duplicate", "qdrant_mysql_mismatch", "point_id_mismatch", "missing_qdrant_point", "missing_mysql_movie"} <= codes
    assert report["status"] == "FAIL"


def test_null_ids_and_orphans_fail():
    movie, row, point = fixture()
    movie["movie_id"] = None
    point["payload"]["movie_id"] = None
    report = module.audit_links([movie], [], [point])
    assert report["status"] == "FAIL"
    assert "orphan_qdrant_point" in {issue["code"] for issue in report["issues"]}


def test_invalid_numeric_ids():
    for value in (True, 0, -1, "UUID", "1.0", 2**63):
        assert module.positive_id(value) is None


def test_empty_inputs_do_not_pass():
    assert module.audit_links([], [], [])["status"] == "FAIL"


def test_live_reader_paginates_and_closes(monkeypatch, tmp_path, capsys):
    import csv
    import json
    from types import SimpleNamespace
    import qdrant_client
    import sys

    movie, row, point = fixture()
    movies = tmp_path / 'movies.jsonl'
    movies.write_text(json.dumps(movie) + '\n')
    export = tmp_path / 'mysql.csv'
    with export.open('w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['id', 'imdb_id', 'tmdb_id'])
        writer.writeheader()
        writer.writerow(row)
    offsets = []
    closed = []

    class Client:
        def __init__(self, **kwargs):
            pass

        def scroll(self, collection, **kwargs):
            offsets.append(kwargs['offset'])
            if kwargs['offset'] is None:
                return [SimpleNamespace(**point)], 'next'
            return [], None

        def close(self):
            closed.append(True)

    monkeypatch.setattr(qdrant_client, 'QdrantClient', Client)
    monkeypatch.setattr(sys, 'argv', ['audit', '--movies', str(movies), '--mysql-csv', str(export),
                                     '--qdrant-url', 'http://fixture.invalid'])
    assert module.main() == 0
    assert offsets == [None, 'next']
    assert closed == [True]
    assert json.loads(capsys.readouterr().out)['status'] == 'PASS'
