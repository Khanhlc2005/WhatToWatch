#!/usr/bin/env python3
"""Score chat filter extraction against a labelled evaluation set."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.services.chat_filters import ExtractedChatFilters, extract_chat_filters


def sha(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def save_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


def filter_atoms(filters):
    result = set()
    data = ExtractedChatFilters.model_validate(filters).model_dump()
    for field, value in data['retrieval'].items():
        if isinstance(value, list):
            result.update((field, item.casefold()) for item in value)
        elif value is not None:
            result.add((field, value))
    for field in ('director', 'actor'):
        if data[field]:
            result.add((field, data[field].casefold()))
    return result


def filter_report(dataset):
    if not dataset['cases'] or len({c['id'] for c in dataset['cases']}) != len(dataset['cases']):
        raise ValueError('Filter cases must have unique IDs')
    totals = Counter()
    fields = {}
    cases = []
    for case in dataset['cases']:
        expected = filter_atoms(case['expected'])
        actual = filter_atoms(extract_chat_filters(case['message']))
        tp, fp, fn = expected & actual, actual - expected, expected - actual
        totals.update(tp=len(tp), fp=len(fp), fn=len(fn), exact=int(expected == actual))
        for field in {name for name, _ in expected | actual}:
            bucket = fields.setdefault(field, Counter())
            bucket.update(tp=sum(name == field for name, _ in tp),
                          fp=sum(name == field for name, _ in fp),
                          fn=sum(name == field for name, _ in fn))
        cases.append({'id': case['id'], 'exact': expected == actual,
                      'tp': sorted(map(list, tp)), 'fp': sorted(map(list, fp)),
                      'fn': sorted(map(list, fn))})

    def scores(counts):
        tp, fp, fn = (counts[key] for key in ('tp', 'fp', 'fn'))
        return {'tp': tp, 'fp': fp, 'fn': fn,
                'precision': tp / (tp + fp) if tp + fp else None,
                'recall': tp / (tp + fn) if tp + fn else None,
                'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None}

    return {'scope': dataset.get('scope'), 'dataset_sha256': sha(dataset),
            'cases': len(cases), 'exact_match_rate': totals['exact'] / len(cases),
            'micro': scores(totals),
            'by_field': {field: scores(counts) for field, counts in sorted(fields.items())},
            'details': cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    command = sub.add_parser('filters')
    command.add_argument('--output', type=Path, required=True)
    command.add_argument('--evaluation', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve evaluation evidence')
    dataset = json.loads(args.evaluation.read_text(encoding='utf-8'))
    save_new(args.output, filter_report(dataset))


if __name__ == '__main__':
    main()
