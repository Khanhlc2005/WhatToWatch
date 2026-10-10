"""Sync confirmed MySQL movie IDs to existing Qdrant payloads without touching vectors.

The default is a read-only plan. --apply takes a Qdrant collection snapshot before
the first write. Conflicting IMDb/TMDB/point identities abort the entire plan.
"""
import argparse
from contextlib import closing
import csv
import json
import os
from pathlib import Path
import re
import sys

from qdrant_client import QdrantClient, models

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'data/scripts'))
from validate_movie_links import positive_id
from uuid import NAMESPACE_URL, uuid5


def expected_ids(mapping_csv, movies_jsonl):
    with mapping_csv.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not {'id', 'imdb_id', 'tmdb_id'}.issubset(reader.fieldnames or []):
            raise ValueError('CSV requires id, imdb_id, tmdb_id')
        rows = list(reader)
    by_imdb = {}
    used_ids = set()
    used_tmdb = set()
    for row in rows:
        imdb = row['imdb_id']
        movie_id = positive_id(row['id'])
        tmdb = positive_id(row['tmdb_id'])
        if not isinstance(imdb, str) or not re.fullmatch(r'tt[0-9]+', imdb) or movie_id is None or tmdb is None or imdb in by_imdb or movie_id in used_ids or tmdb in used_tmdb:
            raise ValueError(f'Invalid or duplicate CSV identity: {imdb}')
        by_imdb[imdb] = (movie_id, tmdb)
        used_ids.add(movie_id)
        used_tmdb.add(tmdb)
    seen = set()
    with movies_jsonl.open(encoding='utf-8') as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            movie = json.loads(line)
            imdb = movie.get('imdb_id')
            if imdb in seen or imdb not in by_imdb:
                raise ValueError(f'Duplicate or unmapped processed IMDb at line {line_number}: {imdb}')
            movie_id, tmdb = by_imdb[imdb]
            if type(movie.get('movie_id')) is not int or movie['movie_id'] != movie_id or positive_id(movie.get('tmdb_id')) != tmdb:
                raise ValueError(f'Processed identity conflicts with CSV: {imdb}')
            seen.add(imdb)
    if seen != set(by_imdb):
        raise ValueError(f'CSV/processed coverage differs: CSV={len(by_imdb)}, processed={len(seen)}')
    return by_imdb


def scan(client, collection, by_imdb):
    pending = []
    seen = set()
    offset = None
    while True:
        points, offset = client.scroll(collection, limit=256, offset=offset,
                                       with_payload=True, with_vectors=False)
        for point in points:
            payload = point.payload or {}
            imdb = payload.get('imdb_id')
            if imdb not in by_imdb or imdb in seen:
                raise ValueError(f'Orphan or duplicate Qdrant IMDb: {imdb}')
            movie_id, tmdb = by_imdb[imdb]
            expected_point = str(uuid5(NAMESPACE_URL, f'whattowatch:movie:{imdb}'))
            if str(point.id) != expected_point or positive_id(payload.get('tmdb_id')) != tmdb:
                raise ValueError(f'Qdrant point/TMDB identity conflicts: {imdb}')
            seen.add(imdb)
            if type(payload.get('movie_id')) is not int or payload['movie_id'] != movie_id:
                pending.append((str(point.id), movie_id))
        if offset is None:
            break
    if seen != set(by_imdb):
        raise ValueError(f'Qdrant coverage differs: expected={len(by_imdb)}, found={len(seen)}')
    return pending


def sync(client, collection, by_imdb, apply=False, batch_size=128):
    pending = scan(client, collection, by_imdb)
    result = {'collection': collection, 'records': len(by_imdb), 'to_update': len(pending),
              'updated': 0, 'failed': 0, 'snapshot': None,
              'status': 'DRY_RUN' if not apply else 'PASS'}
    if not apply or not pending:
        return result
    snapshot = client.create_snapshot(collection, wait=True)
    if snapshot is None or not snapshot.name:
        raise RuntimeError('Qdrant snapshot failed; no payload was written')
    result['snapshot'] = snapshot.name
    try:
        for start in range(0, len(pending), batch_size):
            chunk = pending[start:start + batch_size]
            operations = [models.SetPayloadOperation(set_payload=models.SetPayload(
                points=[point_id], payload={'movie_id': movie_id}))
                for point_id, movie_id in chunk]
            client.batch_update_points(collection, update_operations=operations, wait=True)
            result['updated'] += len(chunk)
        remaining = scan(client, collection, by_imdb)
        result['failed'] = len(remaining)
        result['status'] = 'PASS' if not remaining else 'FAIL'
    except Exception:
        try:
            result['failed'] = len(scan(client, collection, by_imdb))
        except Exception:
            result['failed'] = None  # Qdrant could not be read; outcome is unknown.
        result['status'] = 'FAIL'
        print(json.dumps(result), flush=True)
        raise
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mysql-csv', type=Path, default=ROOT / 'data/processed/movies_id_mapping.csv')
    parser.add_argument('--movies', type=Path, default=ROOT / 'data/processed/movies_with_mysql_ids.jsonl')
    parser.add_argument('--url', default=os.getenv('QDRANT_URL', 'http://127.0.0.1:6335'))
    parser.add_argument('--collection', default=os.getenv('QDRANT_COLLECTION', 'movies'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--batch-size', type=int, default=128)
    args = parser.parse_args()
    if args.batch_size < 1:
        parser.error('--batch-size must be positive')
    by_imdb = expected_ids(args.mysql_csv, args.movies)
    with closing(QdrantClient(url=args.url, timeout=120)) as client:
        result = sync(client, args.collection, by_imdb, apply=args.apply, batch_size=args.batch_size)
    print(json.dumps(result))
    return 0 if result['status'] != 'FAIL' else 1


if __name__ == '__main__':
    raise SystemExit(main())
