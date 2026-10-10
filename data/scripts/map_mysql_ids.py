"""Join a confirmed MySQL export to a catalog without changing either input."""
import argparse
import csv
import filecmp
import hashlib
import json
import os
from pathlib import Path
import tempfile

from validate_movie_links import audit_links, load_jsonl


def map_movies(movies, rows):
    report = audit_links([], rows)
    errors = [item for item in report['issues'] if item['code'] != 'empty_source']
    if errors:
        raise ValueError(f'Invalid MySQL export: {errors[:5]}')
    lookup = {row['imdb_id']: row for row in rows}
    mapped = []
    for movie in movies:
        row = lookup.get(movie['imdb_id'])
        if row is None or str(movie['tmdb_id']) != row['tmdb_id']:
            raise ValueError(f'Missing or conflicting identity: {movie["imdb_id"]}')
        if movie.get('movie_id') not in (None, int(row['id'])):
            raise ValueError(f'Existing movie_id conflicts: {movie["imdb_id"]}')
        mapped.append({**movie, 'movie_id': int(row['id'])})
    report = audit_links(mapped, rows)
    if report['issues']:
        raise ValueError(f'Invalid mapped catalog: {report["issues"][:5]}')
    return mapped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--movies', type=Path, required=True)
    parser.add_argument('--mysql-csv', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with args.mysql_csv.open(encoding='utf-8-sig', newline='') as source:
        reader = csv.DictReader(source)
        if not {'id', 'imdb_id', 'tmdb_id'}.issubset(reader.fieldnames or []):
            parser.error('CSV requires id,imdb_id,tmdb_id')
        rows = list(reader)
    mapped = map_movies(load_jsonl(args.movies), rows)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=args.output.parent, delete=False) as target:
            temporary = Path(target.name)
            for movie in mapped:
                target.write(json.dumps(movie, ensure_ascii=False, sort_keys=True) + '\n')
        if args.output.exists():
            if not filecmp.cmp(temporary, args.output, shallow=False):
                parser.error('Output exists with different content; refusing overwrite')
            status = 'unchanged'
        else:
            os.link(temporary, args.output)  # Atomic publish, refusing existing output.
            status = 'created'
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    print(json.dumps({'status': status, 'mapped': len(mapped), 'mysql_rows': len(rows), 'output': str(args.output),
                      'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__ == '__main__':
    main()
