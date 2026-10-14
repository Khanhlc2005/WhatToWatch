#!/usr/bin/env python3
"""Read-only HTTP evaluation; exports unjudged pooled results, quality metrics only for fully reviewed pools."""
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

MODES = ('dense', 'sparse', 'hybrid', 'hybrid_reranker')


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


def check_hits(hits, catalog, filters, rerank=False):
    issues, seen = [], set()
    previous = math.inf
    missing_text = False
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
        if rerank:
            retrieval_score = hit.get('retrieval_score')
            rerank_score = hit.get('rerank_score')
            if type(retrieval_score) not in (int, float) or not math.isfinite(retrieval_score):
                issues.append('invalid_retrieval_score')
            if rerank_score is None:
                missing_text = True
                if score != retrieval_score: issues.append('fallback_score_mismatch')
            else:
                if missing_text: issues.append('rerank_after_unscored')
                if score != rerank_score: issues.append('rerank_score_mismatch')

        if type(score) not in (int, float) or not math.isfinite(score):
            issues.append('invalid_score')
        else:
            if not (rerank and hit.get('rerank_score') is None):
                if score > previous: issues.append('score_order')
                previous = score
    return issues



def response_hits(run):
    response = run.get('response')
    hits = response.get('hits') if isinstance(response, dict) else None
    return [hit for hit in hits if isinstance(hit, dict)] if isinstance(hits, list) else []


def export_tables(runs, catalog, output):
    pooled = {}
    comparison = ['# Ranking comparison (unjudged)', '', 'Scores across modes are not comparable.', '']
    for run in runs:
        qid, mode = run['query_id'], run['mode']
        comparison += [f"## {qid} / {mode}: {run['query']}", '',
                       '| Rank | movie_id | Title | Score |', '|---|---|---|---|']
        for rank, hit in enumerate(response_hits(run), 1):
            mid = hit.get('movie_id')
            if type(mid) is not int or mid not in catalog:
                continue  # Invalid identities remain in raw evidence, not the review pool.
            movie = catalog[mid]
            comparison.append(f"| {rank} | {mid} | {str(hit.get('title', '')).replace('|', '/')} | {hit.get('score')} |")
            key = (qid, mid)
            row = pooled.setdefault(key, dict(query_id=qid, query=run['query'], filters=json.dumps(run['filters']),
                movie_id=mid, imdb_id=movie.get('imdb_id'), title=movie.get('title'),
                overview=movie.get('overview'), relevance='', reviewer='', notes='',
                **{f'{m}_{field}': '' for m in MODES for field in ('rank', 'score')}))
            row[f'{mode}_rank'], row[f'{mode}_score'] = rank, hit.get('score')
        comparison.append('')
    fields = ['query_id','query','filters','movie_id','imdb_id','title','overview'] + [f'{m}_{f}' for m in MODES for f in ('rank','score')] + ['relevance','reviewer','notes']
    with (output / 'manual_evaluation.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields); writer.writeheader(); writer.writerows(pooled.values())
    (output / 'ranking_comparison.md').write_text('\n'.join(comparison), encoding='utf-8')



def load_labels(path, query_ids, catalog, queries=None):
    """Reviewer attribution is required; anchors/expected IDs never become labels."""
    labels = {}
    with path.open(encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            if not row.get('relevance', '').strip() and not row.get('reviewer', '').strip():
                continue
            qid = row['query_id']
            mid = int(row['movie_id'])
            grade = row['relevance'].strip()
            if qid not in query_ids or mid not in catalog or grade not in ('0', '1', '2', '3') or not row.get('reviewer', '').strip():
                raise ValueError('Invalid or unattributed relevance label')
            if queries is not None:
                query = queries[qid]
                if row.get('query') != query['query'] or json.loads(row.get('filters', 'null')) != query['filters']:
                    raise ValueError('Judgment query/filter mismatch')
            key = (qid, mid)
            if key in labels:
                raise ValueError('Duplicate relevance judgment')
            labels[key] = int(grade)
    return labels


def quality_metrics(runs, labels, k):
    """Pooled nDCG, P and MRR: omit a query unless every compared hit is judged.

    Recall is deliberately absent: judged pools are not exhaustive catalog truth.
    """
    results, skipped = [], {}
    for qid in dict.fromkeys(r['query_id'] for r in runs):
        group = [r for r in runs if r['query_id'] == qid]
        if any(r.get('issues') or r.get('error') for r in group):
            skipped[qid] = 'structural/request failure'; continue
        pool = {h.get('movie_id') for r in group for h in response_hits(r)[:k]}
        judgments = {mid: grade for (q, mid), grade in labels.items() if q == qid}
        if not pool or not pool.issubset(judgments) or not any(judgments.values()):
            skipped[qid] = 'incomplete/empty judgments or no judged positives'; continue
        ideal = sorted(judgments.values(), reverse=True)[:k]
        idcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
        for run in group:
            grades = [judgments[h['movie_id']] for h in run['response']['hits'][:k]]
            dcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(grades))
            results.append(dict(query_id=qid, mode=run['mode'], precision_at_k=sum(g > 0 for g in grades) / k,
                mrr_at_k=next((1 / (i + 1) for i, g in enumerate(grades) if g > 0), 0), ndcg_at_k=dcg / idcg))
    return dict(k=k, scope='Reviewed pool only; not exhaustive catalog relevance.', results=results, skipped=skipped)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--queries', type=Path, default=Path('data/evaluation/query_set_v1.json'))
    p.add_argument('--movies', type=Path, default=Path('data/processed/movies_with_mysql_ids.jsonl'))
    p.add_argument('--mysql-csv', type=Path, default=Path('data/processed/movies_id_mapping.csv'))
    p.add_argument('--base-url', default='http://127.0.0.1:8010')
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--modes', nargs='+', choices=MODES, default=list(MODES[:3]))
    p.add_argument('--candidate-k', type=int, default=50)
    p.add_argument('--labels', type=Path, help='Reviewed pooled CSV, relevance 0..3 plus reviewer')
    args = p.parse_args()
    if len(args.modes) != len(set(args.modes)): p.error('duplicate modes')
    if not 1 <= args.candidate_k <= 500: p.error('candidate-k must be 1..500')
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
    if type(query_set['limit']) is not int or not 1 <= query_set['limit'] <= 100:
        raise ValueError('Invalid final K')
    if 'hybrid_reranker' in args.modes and args.candidate_k < query_set['limit']:
        raise ValueError('candidate K must cover final K')
    labels = load_labels(args.labels, set(ids), catalog, {q['id']: q for q in query_set['queries']}) if args.labels else {}
    args.output.mkdir(parents=True)
    runs = []
    for q in query_set['queries']:
        for mode in args.modes:
            body = dict(query=q['query'], filters=q['filters'], limit=query_set['limit'],
                        mode='hybrid' if mode == 'hybrid_reranker' else mode)
            if mode == 'hybrid_reranker': body.update(rerank=True, candidate_k=args.candidate_k)
            run = dict(query_id=q['id'], **body)
            run['mode'] = mode
            run['request'] = body
            start = time.perf_counter()
            try:
                request = urllib.request.Request(args.base_url.rstrip('/') + '/internal/qdrant/search',
                    data=json.dumps(body).encode(), headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(request, timeout=180) as response:
                    run['response'] = json.load(response)
                hits = run['response']['hits']
                run['issues'] = check_hits(hits, catalog, q['filters'], mode == 'hybrid_reranker')
                if run['response']['mode'] != body['mode']: run['issues'].append('mode_mismatch')
                if len(hits) > query_set['limit']: run['issues'].append('limit_violation')
                if q.get('structural_expectation') == 'empty' and hits: run['issues'].append('expected_empty')
            except Exception as exc:
                run['error'] = type(exc).__name__ + ': ' + str(exc)
                run['issues'] = ['request_failed']
            run['elapsed_seconds'] = round(time.perf_counter() - start, 4)
            runs.append(run)
            with (args.output / 'results.jsonl').open('a') as f: f.write(json.dumps(run, ensure_ascii=False) + '\n')
            print(q['id'], mode, len(response_hits(run)), run['issues'], flush=True)
    export_tables(runs, catalog, args.output)
    metrics = quality_metrics(runs, labels, query_set['limit'])
    (args.output / 'quality_metrics.json').write_text(json.dumps(metrics, indent=2))
    summary = dict(timestamp=datetime.now(timezone.utc).isoformat(), base_url=args.base_url,
        catalog_count=len(movies), queries=len(ids), requests=len(runs), failed_checks=sum(bool(r['issues']) for r in runs),
        sha256={str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.movies,args.mysql_csv,args.queries)},
        relevance='reviewed pools' if metrics['results'] else 'no eligible labels; no quality metrics',
        modes=args.modes, candidate_k=args.candidate_k, labels_sha256=hashlib.sha256(args.labels.read_bytes()).hexdigest() if args.labels else None, latency='single sequential pass, includes cold model startup; not a benchmark')
    (args.output / 'summary.json').write_text(json.dumps(summary, indent=2))
    return int(summary['failed_checks'] > 0)


if __name__ == '__main__':
    raise SystemExit(main())
