#!/usr/bin/env python3
"""Read-only HTTP evaluation; exports unjudged pooled results, never relevance metrics."""
import argparse
import csv
import hashlib
import json
import math
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from validate_movie_links import audit_links, load_jsonl

MODES = ('dense', 'sparse', 'hybrid')


def matches(movie, filters):
    genres = {g['name'] for g in movie.get('genres', [])}
    countries = {c['iso_3166_1'] for c in movie.get('production_countries', [])}
    year = int(movie['release_date'][:4]) if movie.get('release_date') else movie.get('imdb_year')
    if filters.get('genres') and not genres.intersection(filters['genres']): return False
    if genres.intersection(filters.get('exclude_genres', [])): return False
    if filters.get('countries') and not countries.intersection(filters['countries']): return False
    if filters.get('languages') and movie.get('original_language') not in filters['languages']: return False
    for key, value, lower in [('year_min', year, True), ('year_max', year, False),
                              ('rating_min', movie.get('imdb_rating'), True),
                              ('runtime_max', movie.get('runtime_minutes'), False)]:
        if key in filters and (value is None or (value < filters[key] if lower else value > filters[key])):
            return False
    return True


def check_hits(hits, catalog, filters):
    issues, seen = [], set()
    previous = math.inf
    for hit in hits:
        mid = hit.get('movie_id')
        if type(mid) is not int or mid not in catalog:
            issues.append('unverified_id'); continue
        if mid in seen: issues.append('duplicate_id')
        seen.add(mid)
        movie = catalog[mid]
        if any(hit.get(k) != movie[k] for k in ('imdb_id', 'tmdb_id')):
            issues.append('identity_mismatch')
        if not matches(movie, filters): issues.append('filter_violation')
        score = hit.get('score')
        if type(score) not in (int, float) or not math.isfinite(score):
            issues.append('invalid_score')
        else:
            if score > previous: issues.append('score_order')
            previous = score
    return issues


def export_tables(runs, catalog, output):
    pooled = {}
    comparison = ['# Ranking comparison (unjudged)', '', 'Scores across modes are not comparable.', '']
    for run in runs:
        qid, mode = run['query_id'], run['mode']
        comparison += [f"## {qid} / {mode}: {run['query']}", '',
                       '| Rank | movie_id | Title | Score |', '|---|---|---|---|']
        for rank, hit in enumerate(run.get('response', {}).get('hits', []), 1):
            mid = hit.get('movie_id')
            movie = catalog.get(mid, {})
            comparison.append(f"| {rank} | {mid} | {str(hit.get('title', '')).replace('|', '/')} | {hit['score']:.6f} |")
            key = (qid, mid)
            row = pooled.setdefault(key, dict(query_id=qid, query=run['query'], filters=json.dumps(run['filters']),
                movie_id=mid, imdb_id=movie.get('imdb_id'), title=movie.get('title'),
                overview=movie.get('overview'), relevance='', reviewer='', notes='',
                **{f'{m}_{field}': '' for m in MODES for field in ('rank', 'score')}))
            row[f'{mode}_rank'], row[f'{mode}_score'] = rank, hit['score']
        comparison.append('')
    fields = ['query_id','query','filters','movie_id','imdb_id','title','overview'] + [f'{m}_{f}' for m in MODES for f in ('rank','score')] + ['relevance','reviewer','notes']
    with (output / 'manual_evaluation.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(pooled.values())
    (output / 'ranking_comparison.md').write_text('\n'.join(comparison), encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--queries', type=Path, default=Path('data/evaluation/query_set_v1.json'))
    p.add_argument('--movies', type=Path, default=Path('data/processed/movies_with_mysql_ids.jsonl'))
    p.add_argument('--mysql-csv', type=Path, default=Path('data/processed/movies_id_mapping.csv'))
    p.add_argument('--base-url', default='http://127.0.0.1:8010')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): p.error('output must be a new directory; preserve previous judgments')
    movies = load_jsonl(args.movies)
    with args.mysql_csv.open(encoding='utf-8-sig') as f: audit = audit_links(movies, list(csv.DictReader(f)))
    if audit['issues']: raise ValueError('Catalog/CSV identity audit failed')
    catalog = {m['movie_id']: m for m in movies}
    query_set = json.loads(args.queries.read_text())
    ids = [q['id'] for q in query_set['queries']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate query IDs')
    for q in query_set['queries']:
        if q['expected_movie_ids'] or q['relevance_status'] != 'unjudged':
            raise ValueError('v1 runner expects unjudged query set')
        for anchor in q['catalog_anchors']:
            movie = catalog.get(anchor['movie_id'])
            if not movie or any(movie[k] != anchor[k] for k in ('imdb_id','tmdb_id','title')):
                raise ValueError('Unverified catalog anchor')
    args.output.mkdir(parents=True)
    runs = []
    for q in query_set['queries']:
        for mode in MODES:
            body = dict(query=q['query'], filters=q['filters'], limit=query_set['limit'], mode=mode)
            run = dict(query_id=q['id'], **body)
            start = time.perf_counter()
            try:
                request = urllib.request.Request(args.base_url.rstrip('/') + '/internal/qdrant/search',
                    data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request, timeout=180) as response:
                    run['response'] = json.load(response)
                hits = run['response']['hits']
                run['issues'] = check_hits(hits, catalog, q['filters'])
                if run['response']['mode'] != mode: run['issues'].append('mode_mismatch')
                if len(hits) > query_set['limit']: run['issues'].append('limit_violation')
                if q.get('structural_expectation') == 'empty' and hits: run['issues'].append('expected_empty')
            except Exception as exc:
                run['error'] = type(exc).__name__ + ': ' + str(exc)
                run['issues'] = ['request_failed']
            run['elapsed_seconds'] = round(time.perf_counter() - start, 4)
            runs.append(run)
            with (args.output / 'results.jsonl').open('a') as f: f.write(json.dumps(run, ensure_ascii=False) + '\n')
            print(q['id'], mode, len(run.get('response', {}).get('hits', [])), run['issues'], flush=True)
    export_tables(runs, catalog, args.output)
    summary = dict(timestamp=datetime.now(timezone.utc).isoformat(), base_url=args.base_url,
        catalog_count=len(movies), queries=len(ids), requests=len(runs), failed_checks=sum(bool(r['issues']) for r in runs),
        sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.movies,args.mysql_csv,args.queries)},
        relevance='unjudged; no quality metrics', latency='single sequential pass, includes cold model startup; not a benchmark')
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2))
    return int(summary['failed_checks'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())
