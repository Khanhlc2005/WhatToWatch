"""Kiểm kê offline, tạo catalog SQLite từ IMDb theo chunk; không gọi mạng."""

import argparse
from collections import Counter
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import sqlite3


def fingerprint(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'bytes': path.stat().st_size,
            'sha256': digest.hexdigest()}


def batches(rows, size=10000):
    while batch := list(itertools.islice(rows, size)):
        yield batch


def tsv(path):
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as source:
        yield from csv.DictReader(source, delimiter='\t', quoting=csv.QUOTE_NONE)


def prepare(raw_dir, database, report_path):
    # Refuse replacement: an existing DB may already contain run checkpoints.
    if database.exists():
        raise ValueError(f'Giữ nguyên database hiện có: {database}')
    database.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    sources = {name: fingerprint(raw_dir / name) for name in
               ('title.basics.tsv.gz', 'title.ratings.tsv.gz', 'links.csv')}
    counts = Counter()
    db = sqlite3.connect(database)
    try:
        db.executescript('''
            CREATE TABLE ratings (imdb_id TEXT PRIMARY KEY, rating REAL, votes INTEGER);
            CREATE TABLE catalog (imdb_id TEXT PRIMARY KEY, imdb_json TEXT NOT NULL,
                                  tmdb_id INTEGER, mapping_source TEXT);
            CREATE TABLE links (imdb_id TEXT, tmdb_id INTEGER, UNIQUE(imdb_id, tmdb_id));
            CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        ''')
        for chunk in batches(tsv(raw_dir / 'title.ratings.tsv.gz')):
            db.executemany('INSERT INTO ratings VALUES (?, ?, ?)',
                           ((r['tconst'], float(r['averageRating']), int(r['numVotes']))
                            for r in chunk if int(r['numVotes']) >= 50))
            db.commit()
        for chunk in batches(tsv(raw_dir / 'title.basics.tsv.gz')):
            counts['input_rows'] += len(chunk)
            candidates = []
            for row in chunk:
                kind = row['titleType']
                if kind not in ('movie', 'tvMovie'):
                    continue
                counts[kind] += 1
                rating = db.execute('SELECT rating, votes FROM ratings WHERE imdb_id=?',
                                    (row['tconst'],)).fetchone()
                if rating:
                    row.update(averageRating=rating[0], numVotes=rating[1])
                    candidates.append((row['tconst'], json.dumps(row)))
            db.executemany('INSERT INTO catalog (imdb_id, imdb_json) VALUES (?, ?)', candidates)
            counts['eligible_imdb_rows'] += len(candidates)
            db.commit()
        with (raw_dir / 'links.csv').open(newline='', encoding='utf-8') as source:
            for chunk in batches(csv.DictReader(source)):
                links = []
                for row in chunk:
                    counts['movielens_rows'] += 1
                    if row['tmdbId'].isdigit() and int(row['tmdbId']) > 0:
                        links.append((f"tt{int(row['imdbId']):07d}", int(row['tmdbId'])))
                db.executemany('INSERT OR IGNORE INTO links VALUES (?, ?)', links)
            db.commit()
        # Ambiguous IMDb or TMDB IDs must not silently choose the first link.
        db.executescript('''
            CREATE INDEX links_tmdb ON links(tmdb_id);
            CREATE TABLE trusted_links AS SELECT imdb_id, min(tmdb_id) AS tmdb_id
              FROM links GROUP BY imdb_id HAVING count(*) = 1;
            DELETE FROM trusted_links WHERE tmdb_id IN
              (SELECT tmdb_id FROM links GROUP BY tmdb_id HAVING count(*) > 1);
            CREATE UNIQUE INDEX trusted_imdb ON trusted_links(imdb_id);
            UPDATE catalog SET tmdb_id = (SELECT tmdb_id FROM trusted_links t
              WHERE t.imdb_id=catalog.imdb_id), mapping_source='movielens32m'
              WHERE imdb_id IN (SELECT imdb_id FROM trusted_links);
        ''')
        counts['mapped_tmdb_rows'] = db.execute(
            'SELECT count(*) FROM catalog WHERE tmdb_id IS NOT NULL').fetchone()[0]
        counts['needs_find_rows'] = counts['eligible_imdb_rows'] - counts['mapped_tmdb_rows']
        counts['ambiguous_link_imdb_ids'] = db.execute(
            'SELECT count(DISTINCT imdb_id) FROM links WHERE imdb_id NOT IN '
            '(SELECT imdb_id FROM trusted_links)').fetchone()[0]
        report = dict(counts, source_file_versions=sources, run_started_at=started,
                      run_completed_at=datetime.now(timezone.utc).isoformat())
        db.execute('INSERT INTO metadata VALUES (?, ?)', ('inventory', json.dumps(report)))
        db.commit()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        return report
    finally:
        db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw-dir', type=Path, default=Path('data/raw'))
    parser.add_argument('--database', type=Path, default=Path('data/processed/catalog.sqlite'))
    parser.add_argument('--report', type=Path, default=Path('data/processed/catalog_inventory.json'))
    args = parser.parse_args()
    print(json.dumps(prepare(args.raw_dir, args.database, args.report), indent=2))
