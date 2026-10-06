"""Pipeline TMDB có checkpoint SQLite, cache bền vững và xuất JSONL theo luồng.

Mặc định offline. Chỉ dùng --dns-confirmed sau xác nhận trực tiếp của người dùng.
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from catalog_lock import catalog_lock
import json
import math
import os
from pathlib import Path
import sqlite3
import time

from clean_movies import clean_movie
from embedding_template import TEXT_TEMPLATE_VERSION


def now():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False)
        output.write('\n')
        output.flush()
        os.fsync(output.fileno())
    temporary.replace(path)


class FetchError(Exception):
    """Messages intentionally contain no request URL, credential or response body."""


class NetworkStopped(FetchError):
    pass


class BudgetStopped(NetworkStopped):
    """A resource limit leaves the current movie pending for a future run."""


def network_error_kind(error):
    """Inspect exception types only; never expose request URLs or credentials."""
    import socket
    import ssl
    pending, seen = [error], set()
    kinds = set()
    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        if isinstance(current, ConnectionResetError):
            kinds.add('connection_reset')
        elif isinstance(current, socket.gaierror):
            kinds.add('dns_resolution')
        elif isinstance(current, ssl.SSLError):
            kinds.add('tls_error')
        for attr in ('__cause__', '__context__', 'reason'):
            child = getattr(current, attr, None)
            if isinstance(child, BaseException):
                pending.append(child)
        pending.extend(item for item in current.args if isinstance(item, BaseException))
    return ','.join(sorted(kinds)) or 'request_error'


class Client:
    def __init__(self, rate=2.0, attempts=4):
        import requests
        from dotenv import load_dotenv
        load_dotenv()
        self.key = os.getenv('TMDB_API')
        if not self.key:
            raise FetchError('missing_TMDB_API')
        if not math.isfinite(rate) or rate <= 0 or attempts < 1:
            raise ValueError('invalid_request_settings')
        self.session = requests.Session()
        self.rate, self.attempts = rate, attempts
        self.last = 0.0
        self.requests = 0

    def get(self, endpoint, **params):
        import requests
        for attempt in range(self.attempts):
            time.sleep(max(0, self.last + 1 / self.rate - time.monotonic()))
            self.last = time.monotonic()
            self.requests += 1
            try:
                response = self.session.get('https://api.themoviedb.org/3/' + endpoint,
                    params=dict(params, api_key=self.key), timeout=(10, 30))
            except requests.RequestException as error:
                if attempt + 1 == self.attempts:
                    raise NetworkStopped('network_retries_exhausted:' + network_error_kind(error)) from None
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError:
                    raise FetchError('invalid_response_json') from None
            if response.status_code in (401, 403):
                raise NetworkStopped('authentication_failed')
            if response.status_code != 429 and response.status_code < 500:
                raise FetchError(f'http_{response.status_code}')
            if attempt + 1 == self.attempts:
                error_type = NetworkStopped if response.status_code == 429 else FetchError
                raise error_type(f'http_{response.status_code}_retries_exhausted')
            delay = 2 ** attempt
            retry = response.headers.get('Retry-After')
            if retry:
                try:
                    seconds = float(retry)
                except ValueError:
                    try:
                        seconds = (parsedate_to_datetime(retry) - datetime.now(timezone.utc)).total_seconds()
                    except (ValueError, TypeError):
                        seconds = 0
                if math.isfinite(seconds):
                    delay = max(delay, seconds)
            # Long rate-limit delays end the batch so the user can restore DNS.
            if delay > 60:
                raise NetworkStopped('retry_after_exceeds_60_seconds')
            time.sleep(delay)


def valid_details(value, imdb_id, tmdb_id):
    return (isinstance(value, dict) and value.get('id') == tmdb_id
            and value.get('imdb_id') == imdb_id
            and isinstance(value.get('credits'), dict)
            and isinstance(value['credits'].get('cast'), list)
            and isinstance(value['credits'].get('crew'), list)
            and isinstance(value.get('keywords'), dict)
            and isinstance(value['keywords'].get('keywords'), list)
            and isinstance(value.get('videos'), dict)
            and isinstance(value['videos'].get('results'), list))


def transform(imdb, tmdb):
    def named(items):
        return [{**item, 'tmdb_id': item.get('id')} for item in items]
    videos = [v for v in tmdb['videos']['results']
              if v.get('site') == 'YouTube' and v.get('type') == 'Trailer' and v.get('key')]
    videos.sort(key=lambda v: (not bool(v.get('official')), v.get('key', '')))
    result = {key: tmdb.get(key) for key in (
        'title', 'original_title', 'overview', 'tagline', 'production_countries',
        'original_language', 'release_date', 'status', 'poster_path', 'backdrop_path')}
    result.update(movie_id=None, imdb_id=imdb['tconst'], tmdb_id=tmdb['id'],
        imdb_title=imdb['primaryTitle'], imdb_year=imdb['startYear'],
        imdb_rating=imdb['averageRating'], imdb_vote_count=imdb['numVotes'],
        imdb_genres=imdb['genres'].split(',') if imdb['genres'] != '\\N' else [],
        adult=imdb['isAdult'], runtime_minutes=tmdb.get('runtime') or imdb['runtimeMinutes'],
        tmdb_vote_average=tmdb.get('vote_average'), tmdb_popularity=tmdb.get('popularity'),
        genres=named(tmdb.get('genres', [])), keywords=named(tmdb['keywords']['keywords']),
        cast=named(tmdb['credits']['cast']),
        directors=named([p for p in tmdb['credits']['crew'] if p.get('job') == 'Director']),
        trailer=videos[0] if videos else None)
    return result


def init_state(db):
    db.executescript('''
        CREATE TABLE IF NOT EXISTS results (
          imdb_id TEXT PRIMARY KEY, tmdb_id INTEGER, status TEXT NOT NULL,
          source_json TEXT, cleaned_json TEXT, reason TEXT, updated_at TEXT);
        CREATE UNIQUE INDEX IF NOT EXISTS results_tmdb
          ON results(tmdb_id) WHERE status='succeeded';
    ''')


def read_cache(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (ValueError, OSError):
        raise FetchError('cache_invalid_preserved') from None


def process_one(db, imdb, tmdb_id, cache, client=None):
    imdb_id = imdb['tconst']
    used_cache = True
    if tmdb_id is None:
        path = cache / 'find' / f'{imdb_id}.json'
        found = read_cache(path)
        if found is None:
            if client is None:
                return 'pending', False
            found = client.get(f'find/{imdb_id}', external_source='imdb_id')
            atomic_json(path, found)
            used_cache = False
        if not isinstance(found, dict) or not isinstance(found.get('movie_results'), list):
            raise FetchError('invalid_find_response')
        matches = found['movie_results']
        if not matches:
            db.execute('INSERT OR REPLACE INTO results VALUES (?,NULL,?,NULL,NULL,NULL,?)',
                       (imdb_id, 'unmatched', now()))
            db.commit()
            return 'unmatched', used_cache
        if len(matches) != 1 or type(matches[0].get('id')) is not int or matches[0]['id'] <= 0:
            raise FetchError('ambiguous_find_response')
        tmdb_id = matches[0]['id']
        db.execute('UPDATE catalog SET tmdb_id=?, mapping_source=? WHERE imdb_id=?',
                   (tmdb_id, 'tmdb_find', imdb_id))
        db.commit()
    path = cache / 'movie' / f'{tmdb_id}.json'
    details = read_cache(path)
    if details is None:
        if client is None:
            return 'pending', False
        details = client.get(f'movie/{tmdb_id}', append_to_response='credits,keywords,videos', language='en-US')
        atomic_json(path, details)  # raw first, transform second
        used_cache = False
    if not valid_details(details, imdb_id, tmdb_id):
        raise FetchError('metadata_incomplete_or_id_mismatch')
    source = transform(imdb, details)
    cleaned = clean_movie(source)
    try:
        db.execute('''INSERT INTO results VALUES (?,?,?,?,?,NULL,?)
            ON CONFLICT(imdb_id) DO UPDATE SET tmdb_id=excluded.tmdb_id,
            status=excluded.status, source_json=excluded.source_json,
            cleaned_json=excluded.cleaned_json, reason=NULL, updated_at=excluded.updated_at''',
            (imdb_id, tmdb_id, 'succeeded', json.dumps(source, ensure_ascii=False),
             json.dumps(cleaned, ensure_ascii=False, sort_keys=True), now()))
        db.commit()
    except sqlite3.IntegrityError:
        db.rollback()
        raise FetchError('duplicate_tmdb_id') from None
    return 'succeeded', used_cache


def run(db, cache, client=None, limit=None, ids=None, retry_failed=False, progress_every=100, prioritize_votes=False, target_successes=None):
    if target_successes is not None and target_successes <= 0:
        raise ValueError('target_successes_must_be_positive')
    init_state(db)
    total_successes = db.execute("SELECT count(*) FROM results WHERE status='succeeded'").fetchone()[0]
    counts = Counter({key: 0 for key in (
        'processed', 'succeeded', 'skipped_from_cache', 'unmatched', 'failed', 'pending', 'already_completed')})
    started = time.monotonic()
    initial_requests = client.requests if client else 0
    eligible = db.execute('SELECT count(*) FROM catalog').fetchone()[0]
    terminal = ('succeeded', 'unmatched') if retry_failed else ('succeeded', 'unmatched', 'failed')
    ordering = "CAST(json_extract(imdb_json, '$.numVotes') AS INTEGER) DESC, imdb_id" if prioritize_votes else 'imdb_id'
    for imdb_id, payload, tmdb_id in db.execute('SELECT imdb_id, imdb_json, tmdb_id FROM catalog ORDER BY ' + ordering):
        if target_successes is not None and total_successes >= target_successes:
            break
        if ids is not None and imdb_id not in ids:
            continue
        state = db.execute('SELECT status FROM results WHERE imdb_id=?', (imdb_id,)).fetchone()
        if state and state[0] in terminal:
            counts['already_completed'] += 1
            continue
        if limit is not None and counts['processed'] >= limit:
            break
        try:
            status, cached = process_one(db, json.loads(payload), tmdb_id, cache, client)
            counts['skipped_from_cache'] += int(cached)
        except BudgetStopped:
            raise
        except (FetchError, ValueError, TypeError, KeyError, AttributeError) as error:
            # No exception string from requests or data is ever emitted.
            reason = str(error) if isinstance(error, FetchError) else type(error).__name__
            tmdb_id = db.execute('SELECT tmdb_id FROM catalog WHERE imdb_id=?', (imdb_id,)).fetchone()[0]
            db.execute('INSERT OR REPLACE INTO results VALUES (?,?,?,NULL,NULL,?,?)',
                       (imdb_id, tmdb_id, 'failed', reason, now()))
            db.commit()
            counts['failed'] += 1
            if isinstance(error, NetworkStopped):
                raise
        else:
            counts[status] += 1
            total_successes += int(status == 'succeeded')
        counts['processed'] += 1
        if counts['processed'] % progress_every == 0:
            print(json.dumps(dict(counts,
                current_request_rate=(client.requests-initial_requests if client else 0) / max(1, time.monotonic()-started),
                estimated_remaining_records=eligible-db.execute('SELECT count(*) FROM results').fetchone()[0])), flush=True)
    return dict(counts)


def export(db, folder):
    """Snapshot files are rebuilt by streaming committed rows, never appended."""
    init_state(db)
    folder.mkdir(parents=True, exist_ok=True)
    inventory = json.loads(db.execute("SELECT value FROM metadata WHERE key='inventory'").fetchone()[0])
    missing = Counter()
    statuses = dict(db.execute('SELECT status, count(*) FROM results GROUP BY status'))
    files = {
        'imdb_tmdb_full.jsonl': ('succeeded', 'source_json'),
        'movies_cleaned_full.jsonl': ('succeeded', 'cleaned_json'),
        'movies_cleaned_full_unmatched.jsonl': ('unmatched', None),
        'movies_cleaned_full_rejected.jsonl': ('failed', None),
    }
    for name, (status, column) in files.items():
        target = folder / name
        temporary = target.with_suffix('.jsonl.tmp')
        with temporary.open('w', encoding='utf-8') as output:
            for imdb_id, tmdb_id, source, cleaned, reason in db.execute(
                'SELECT imdb_id, tmdb_id, source_json, cleaned_json, reason FROM results WHERE status=? ORDER BY imdb_id', (status,)):
                line = source if column == 'source_json' else cleaned if column else json.dumps(
                    dict(imdb_id=imdb_id, tmdb_id=tmdb_id, reason=reason))
                output.write(line + '\n')
                if column == 'cleaned_json':
                    missing.update(json.loads(line)['missing_fields'])
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(target)
    pending = inventory['eligible_imdb_rows'] - sum(statuses.values())
    report = dict(inventory, mapped_tmdb_rows=db.execute('SELECT count(*) FROM catalog WHERE tmdb_id IS NOT NULL').fetchone()[0],
        unmatched_tmdb_rows=statuses.get('unmatched', 0), output_rows=statuses.get('succeeded', 0),
        rejected_rows=statuses.get('failed', 0), pending_rows=pending,
        duplicate_imdb_ids=0, duplicate_tmdb_ids=0, missing_by_field=dict(missing),
        text_template_version=TEXT_TEMPLATE_VERSION,
        run_completed_at=now() if not pending and not statuses.get('failed') else None,
        complete=not pending and not statuses.get('failed'))
    atomic_json(folder / 'movies_cleaned_full_report.json', report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, default=Path('data/processed/catalog.sqlite'))
    parser.add_argument('--cache', type=Path, default=Path('data/processed/tmdb_cache'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--ids', type=Path, help='Một IMDb ID mỗi dòng, dùng cho dry run')
    parser.add_argument('--rate', type=float, default=2.0)
    parser.add_argument('--dns-confirmed', action='store_true')
    parser.add_argument('--retry-failed', action='store_true')
    args = parser.parse_args()
    if not args.database.is_file():
        parser.error('Chạy catalog_inventory.py trước')
    if args.limit is not None and args.limit < 1:
        parser.error('--limit phải > 0')
    with catalog_lock(args.database.with_suffix('.lock')):
        db = sqlite3.connect(args.database)
        try:
            client = Client(args.rate) if args.dns_confirmed else None
            if client:
                # Exactly one read-only connectivity probe, with no retry.
                attempts = client.attempts
                client.attempts = 1
                client.get('configuration')
                client.attempts = attempts
            ids = set(args.ids.read_text().split()) if args.ids else None
            print(json.dumps(run(db, args.cache, client, args.limit, ids, args.retry_failed)))
            if args.output:
                print(json.dumps(export(db, args.output)))
        except NetworkStopped as error:
            print(f'Dừng batch: {error}', flush=True)
            raise SystemExit(2) from None
        finally:
            db.close()
            if args.dns_confirmed:
                print('Giai đoạn gọi TMDB đã dừng/hoàn thành. Bạn có thể chuyển DNS về cấu hình ban đầu.', flush=True)


if __name__ == '__main__':
    main()
