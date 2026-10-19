#!/usr/bin/env python3
"""Freeze catalog contexts, capture an already-installed model, compare paired RAG outputs.

No model pulls, runtime changes, training, or invented relevance judgments.
PYTHONPATH=ai-service is required. Scores describe contract checks, not semantic quality.
"""
import argparse
import hashlib
import json
import time
import urllib.request
from pathlib import Path

from app.schemas.chat import ChatRequest
from app.schemas.rag import MovieContext, RAGAnswer
from app.services.rag import SYSTEM_PROMPT, build_user_prompt, parse_answer, answer_question


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def prepare(queries, catalog, sft):
    training_ids = {json.loads(line)['provenance']['source_movie_id'] for line in sft.read_text().splitlines()}
    cases = []
    for q in queries['queries']:
        context = []
        for anchor in q['catalog_anchors']:
            mid = anchor['movie_id']
            if mid in training_ids: raise ValueError('Chatbot evaluation anchor overlaps SFT train')
            m = catalog[mid]
            if any(m[k] != anchor[k] for k in ('imdb_id', 'tmdb_id', 'title')):
                raise ValueError('Unverified anchor')
            context.append(MovieContext(movie_id=str(mid), title=m['title'],
                genres=[g['name'] for g in m.get('genres', [])], overview=m.get('overview') or None,
                director=', '.join(d['name'] for d in m.get('directors', [])) or None,
                runtime_minutes=m.get('runtime_minutes'), imdb_rating=m.get('imdb_rating')).model_dump(exclude_none=True))
        cases.append(dict(id=q['id'], question=q['query'], context=context, category='fixed_context',
                          provenance='Verified catalog anchors; context inclusion is not a relevance label.'))
    # Structural cases have no relevance or user feedback labels.
    context = next(c['context'] for c in cases if c['context'])
    cases.extend([
        dict(id='C19', question='Who directed this movie?', context=context, category='fact'),
        dict(id='C20', question='Recommend a movie.', context=[], category='empty_context', expected_status='insufficient_context'),
        dict(id='C21', question='Who directed this movie?', context=[dict(movie_id=context[0]['movie_id'], title=context[0]['title'])],
             category='missing_fact', expected_status='insufficient_context'),
        dict(id='C22', question='What genres does this movie belong to?', context=context, category='fact'),
    ])
    return dict(version='chatbot_v1', scope='Fixed catalog context; no retrieval or personalized recommendation gain claims.',
        source_queries_sha256=sha(queries), source_catalog_sha256=sha(catalog),
        sft_train_sha256=hashlib.sha256(sft.read_bytes()).hexdigest(), cases=cases)


def checks(raw, context):
    result = dict(json_contract=False, source_identity=False, reason_fact_support=None)
    try:
        # Check original output before parser can normalize fallback text.
        RAGAnswer.model_validate(json.loads(raw))
        result['json_contract'] = True
        parsed = parse_answer(raw, context)
        result['source_identity'] = True
        sources = {m.movie_id: m for m in context}
        result['reason_fact_support'] = all(any(f.casefold() in hit.reason.casefold() for f in
            [*sources[hit.movie_id].genres, sources[hit.movie_id].director or '', sources[hit.movie_id].overview or ''] if f)
            for hit in parsed.movies) if parsed.movies else None
    except (ValueError, TypeError):
        pass
    return result


def capture(dataset, model, url):
    def request(path, body=None):
        req = urllib.request.Request(url.rstrip('/') + path,
            data=json.dumps(body).encode() if body is not None else None,
            headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=300) as response: return json.load(response)
    installed = request('/api/tags')['models']
    match = next((m for m in installed if m['name'] == model), None)
    if not match: raise ValueError('Model must already be installed; this runner never pulls models')
    runs = []
    for case in dataset['cases']:
        chat_request = ChatRequest.model_validate({
            'message': case['question'], 'movie_context': case['context'],
            'history': case.get('history', []), 'summary': case.get('summary'),
        })
        context = chat_request.movie_context or []
        history = chat_request.history
        summary = chat_request.summary
        generations = []
        def generate(prompt, system):
            response = request('/api/generate', dict(model=model, prompt=prompt, system=system,
                stream=False, format=RAGAnswer.model_json_schema(), options={'temperature': 0, 'seed': 42, 'num_predict': 512}))
            raw = response['response']
            generations.append(dict(raw=raw, prompt_sha256=sha(dict(prompt=prompt, system=system)), checks=checks(raw, context)))
            return raw
        run = dict(id=case['id'], input_sha256=sha(case), generations=generations)
        start = time.perf_counter()
        try:
            # Capture a first raw output for all cases, including those short-circuited by the guard.
            first_prompt = build_user_prompt(case['question'], context, history, summary)
            generate(first_prompt, SYSTEM_PROMPT)
            first_raw = generations[0]['raw']
            consumed = False
            def replay_then_generate(prompt, system):
                nonlocal consumed
                if not consumed:
                    consumed = True
                    return first_raw
                return generate(prompt, system)
            result = answer_question(case['question'], context, replay_then_generate,
                                     history=history, summary=summary)
            run['guarded_response'] = result.model_dump()
            run['guarded_checks'] = checks(result.model_dump_json(), context)
            if 'expected_status' in case:
                run['structural_status_match'] = result.status == case['expected_status']
            if 'expected_movie_ids' in case:
                run['memory_movie_ids_match'] = (
                    [movie.movie_id for movie in result.movies] == case['expected_movie_ids'])
        except Exception as exc:
            run['error'] = type(exc).__name__ + ': ' + str(exc)
        run['elapsed_seconds'] = time.perf_counter() - start
        runs.append(run)
    return dict(model=model, model_digest=match.get('digest'), evaluation_sha256=sha(dataset),
        system_prompt_sha256=sha(SYSTEM_PROMPT), generation_options={'temperature': 0, 'seed': 42, 'num_predict': 512}, runs=runs)


def compare(dataset, base, tuned):
    for artifact in (base, tuned):
        if artifact['evaluation_sha256'] != sha(dataset) or artifact['system_prompt_sha256'] != sha(SYSTEM_PROMPT):
            raise ValueError('Evaluation/system prompt mismatch')
    if base['generation_options'] != tuned['generation_options']:
        raise ValueError('Generation options mismatch')
    indexed = []
    for artifact in (base, tuned):
        rows = {r['id']: r for r in artifact['runs']}
        if len(rows) != len(artifact['runs']) or set(rows) != {c['id'] for c in dataset['cases']}:
            raise ValueError('Incomplete/duplicate capture IDs')
        if any(rows[c['id']]['input_sha256'] != sha(c) for c in dataset['cases']):
            raise ValueError('Frozen input mismatch')
        indexed.append(rows)
    paired = []
    for case in dataset['cases']:
        a, b = (index[case['id']] for index in indexed)
        paired.append(dict(id=case['id'], base=a, finetuned=b))
    return dict(scope='Structural checks only; reason substring checks are not semantic explainability judgments.',
        quality_metrics=None, reason='No human-reviewed relevance/answer/explanation labels supplied.',
        evaluation_sha256=sha(dataset), base_model=base['model'], finetuned_model=tuned['model'],
        base_model_digest=base.get('model_digest'), finetuned_model_digest=tuned.get('model_digest'),
        paired=paired)


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2); stream.write('\n')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--queries', type=Path, default=Path('data/evaluation/query_set_v1.json'))
    prep.add_argument('--movies', type=Path, default=Path('data/processed/movies_with_mysql_ids.jsonl'))
    prep.add_argument('--sft-train', type=Path, default=Path('finetuning/datasets/v2-en/train.jsonl'))
    prep.add_argument('--output', type=Path, required=True)
    run = sub.add_parser('capture')
    run.add_argument('--evaluation', type=Path, required=True)
    run.add_argument('--model', required=True)
    run.add_argument('--ollama-url', default='http://localhost:11434')
    run.add_argument('--output', type=Path, required=True)
    comp = sub.add_parser('compare')
    comp.add_argument('--evaluation', type=Path, required=True)
    comp.add_argument('--base', type=Path, required=True)
    comp.add_argument('--finetuned', type=Path, required=True)
    comp.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    if args.output.exists(): p.error('output already exists; preserve evidence')
    if args.command == 'prepare':
        movies = [json.loads(line) for line in args.movies.read_text().splitlines()]
        catalog = {m['movie_id']: m for m in movies}
        if len(catalog) != len(movies): raise ValueError('Duplicate catalog IDs')
        result = prepare(json.loads(args.queries.read_text()), catalog, args.sft_train)
    elif args.command == 'capture':
        result = capture(json.loads(args.evaluation.read_text()), args.model, args.ollama_url)
    else:
        result = compare(json.loads(args.evaluation.read_text()), json.loads(args.base.read_text()), json.loads(args.finetuned.read_text()))
    write_new(args.output, result)
    return int(any(r.get('error') for r in result.get('runs', [])))


if __name__ == '__main__':
    raise SystemExit(main())
