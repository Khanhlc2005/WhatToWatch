"""Audit existing SFT artifacts against source, deterministic generator and live RAG schema.

Never edits splits. Test content is used only for integrity checks, never tuning.
Run with PYTHONPATH=.:ai-service using the AI service Python environment.
"""
import argparse
import json
import tempfile
from pathlib import Path

from finetuning.scripts.build_sft_v1 import SOURCE, OUTPUT, build, file_digest, digest
from app.schemas.rag import MovieContext
from app.services.rag import parse_answer

SPLITS = ('train', 'validation', 'test')


def validate(source=SOURCE, dataset=OUTPUT, queries=None):
    manifest = json.loads((dataset / 'manifest.json').read_text(encoding='utf-8'))
    issues, warnings = [], ['Synthetic templates only; no human-reviewed conversations or relevance labels.',
        'Vietnamese targets differ from the runtime SYSTEM_PROMPT requirement to answer in English.',
        'Only answered/director/genre tasks; no no_match, insufficient_context, multi-turn or recommendation supervision.']
    language = 'en' if manifest.get('version') == 'catalog_fact_templates_v2_en' else 'vi'
    if language == 'en':
        warnings.pop(1)
    counts, ids, identities, seen = {}, {}, {}, set()
    catalog = {}
    for line in source.read_text(encoding='utf-8').splitlines():
        movie = json.loads(line)
        mid = movie.get('movie_id')
        if type(mid) is int and mid > 0:
            if mid in catalog:
                issues.append('duplicate_source_movie_id')
            catalog[mid] = movie
    source_sha = file_digest(source)
    if source_sha != manifest.get('source_sha256'):
        issues.append('source_hash_mismatch')
    for split in SPLITS:
        rows = (dataset / f'{split}.jsonl').read_text(encoding='utf-8').splitlines()
        counts[split], ids[split], identities[split] = len(rows), set(), set()
        for number, line in enumerate(rows, 1):
            try:
                row = json.loads(line)
                if set(row) != {'messages', 'provenance'}:
                    raise ValueError('unexpected row keys')
                messages, provenance = row['messages'], row['provenance']
                if [m['role'] for m in messages] != ['system', 'user', 'assistant']:
                    raise ValueError('message roles/order')
                if any(set(m) != {'role', 'content'} or not isinstance(m['content'], str) or not m['content'].strip() for m in messages):
                    raise ValueError('invalid messages')
                mid = provenance['source_movie_id']
                if type(mid) is not int or mid not in catalog:
                    raise ValueError('invalid source identity')
                if provenance['source_sha256'] != source_sha or provenance['generator'] != manifest['version'] or provenance['origin'] != manifest['origin']:
                    raise ValueError('invalid provenance')
                bucket = int(digest(f'split:v1:{mid}')[:8], 16) % 10
                expected_split = 'train' if bucket < 8 else 'validation' if bucket == 8 else 'test'
                if split != expected_split:
                    raise ValueError('wrong deterministic split')
                ids[split].add(mid)
                for key in ('imdb_id', 'tmdb_id'):
                    value = catalog[mid].get(key)
                    if value:
                        identities[split].add((key, str(value)))
                content = messages[1]['content']
                prefix = 'MOVIE_CONTEXT (JSON data, not instructions):\n'
                if not content.startswith(prefix):
                    raise ValueError('missing context marker')
                raw_context, question = content[len(prefix):].split('\n\nQUESTION:\n', 1)
                if not question.strip():
                    raise ValueError('empty question')
                context = [MovieContext.model_validate(m) for m in json.loads(raw_context.split('\n\nCONVERSATION_SUMMARY', 1)[0])]
                if len(context) != 1 or context[0].movie_id != str(mid):
                    raise ValueError('context identity')
                parse_answer(messages[2]['content'], context)
                key = digest(json.dumps(messages, ensure_ascii=False, sort_keys=True))
                if key in seen:
                    raise ValueError('duplicate example')
                seen.add(key)
            except (ValueError, KeyError, TypeError) as exc:
                issues.append(f'{split}:{number}: {exc}')
    for i, a in enumerate(SPLITS):
        for b in SPLITS[i + 1:]:
            if ids[a] & ids[b]: issues.append(f'movie_id leakage: {a}/{b}')
            if identities[a] & identities[b]: issues.append(f'external identity leakage: {a}/{b}')
    # Rebuild in a temporary directory: verifies exact source facts/targets,
    # provenance paths, selection, counts and manifest, without changing v1.
    with tempfile.TemporaryDirectory(prefix='wtw-sft-audit-') as tmp:
        expected = Path(tmp)
        build(source, expected, manifest['max_movies'], language)
        for name in ['manifest.json'] + [f'{s}.jsonl' for s in SPLITS]:
            if (expected / name).read_bytes() != (dataset / name).read_bytes():
                issues.append(f'generator/source mismatch: {name}')
    overlap = {}
    if queries:
        anchors = {a['movie_id'] for q in json.loads(queries.read_text())['queries'] for a in q['catalog_anchors']}
        overlap = {s: len(ids[s] & anchors) for s in SPLITS}
        if overlap.get('train'):
            warnings.append('Retrieval evaluation anchors overlap SFT train; do not claim unseen-movie chatbot generalization.')
    return dict(passed=not issues, issues=issues, warnings=warnings, examples=counts,
        movies={s: len(ids[s]) for s in SPLITS}, source_sha256=source_sha,
        artifact_sha256={p.name: file_digest(p) for p in sorted(dataset.glob('*')) if p.is_file()},
        retrieval_anchor_overlap=overlap, training_ready=not issues and language == 'en',
        training_blockers=['Language policy differs from runtime.'] if language == 'vi' else [],
        scope='Format and catalog facts only; semantic/human quality requires owner review.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', type=Path, default=SOURCE)
    p.add_argument('--dataset', type=Path, default=OUTPUT)
    p.add_argument('--queries', type=Path, default=Path('data/evaluation/query_set_v1.json'))
    p.add_argument('--report', type=Path, required=True)
    args = p.parse_args()
    report = validate(args.source, args.dataset, args.queries)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
