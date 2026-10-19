#!/usr/bin/env python3
"""Score filter extraction, fixed-context memory, and reviewed chatbot answers.

Semantic quality is reported only after a reviewer labels every paired output.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from app.schemas.rag import RAGAnswer
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


def validate_comparison(dataset, comparison):
    if comparison['evaluation_sha256'] != sha(dataset):
        raise ValueError('Comparison does not match the evaluation dataset')
    if comparison['base_model'] == comparison['finetuned_model'] or (
        comparison.get('base_model_digest') and
        comparison['base_model_digest'] == comparison.get('finetuned_model_digest')
    ):
        raise ValueError('Base and fine-tuned captures identify the same model')
    cases = {case['id']: case for case in dataset['cases']}
    paired = comparison['paired']
    if not cases or len(cases) != len(dataset['cases']) or len(paired) != len(cases):
        raise ValueError('Missing or duplicate evaluation cases')
    if {row['id'] for row in paired} != set(cases):
        raise ValueError('Comparison has missing or unknown IDs')
    for row in paired:
        for model in ('base', 'finetuned'):
            if row[model]['input_sha256'] != sha(cases[row['id']]):
                raise ValueError('Comparison input hash mismatch')
    return cases


def ordered_outputs(row):
    models = ('base', 'finetuned') if int(sha(row['id'])[0], 16) % 2 == 0 else ('finetuned', 'base')
    result = []
    for slot, model in zip(('A', 'B'), models):
        run = row[model]
        output = {'raw': run['generations'][0]['raw'] if run.get('generations') else None,
                  'guarded': run.get('guarded_response')}
        result.append({'slot': slot, 'output_sha256': sha(output), **output})
    return result


def review_template(dataset, comparison):
    cases = validate_comparison(dataset, comparison)
    return {'version': 'chat_answer_review_v1', 'evaluation_sha256': sha(dataset),
            'rubric': {'faithful': 'true only if all factual claims are supported by context',
                       'relevance': '0 irrelevant, 1 weak, 2 relevant, 3 directly answers the question'},
            'cases': [
                {'id': row['id'], 'question': cases[row['id']]['question'],
                 'context': cases[row['id']]['context'],
                 'outputs': [{**output, 'reviewer': None,
                              'labels': {'raw': {'faithful': None, 'relevance': None},
                                         'guarded': {'faithful': None, 'relevance': None}},
                              'notes': ''} for output in ordered_outputs(row)]}
                for row in comparison['paired']]}


def review_report(dataset, comparison, review):
    template = review_template(dataset, comparison)
    if review.get('version') != template['version'] or review.get('evaluation_sha256') != template['evaluation_sha256']:
        raise ValueError('Review version or dataset hash mismatch')
    review_rows = {row['id']: row for row in review.get('cases', [])}
    if len(review_rows) != len(template['cases']) or len(review['cases']) != len(review_rows):
        raise ValueError('Review cases are missing or duplicated')
    totals = {model: {stage: Counter() for stage in ('raw', 'guarded')}
              for model in ('base', 'finetuned')}
    for expected in template['cases']:
        supplied = review_rows.get(expected['id'])
        if supplied is None or supplied.get('question') != expected['question'] or supplied.get('context') != expected['context']:
            raise ValueError(f"Review input changed: {expected['id']}")
        outputs = {output['slot']: output for output in supplied.get('outputs', [])}
        if len(outputs) != 2 or len(supplied['outputs']) != 2:
            raise ValueError(f"Review outputs missing or duplicated: {expected['id']}")
        model_order = ('base', 'finetuned') if int(sha(expected['id'])[0], 16) % 2 == 0 else ('finetuned', 'base')
        for expected_output, model in zip(expected['outputs'], model_order):
            output = outputs.get(expected_output['slot'])
            if output is None or any(output.get(key) != expected_output[key] for key in
                                     ('output_sha256', 'raw', 'guarded')):
                raise ValueError(f"Review output changed: {expected['id']}")
            if not isinstance(output.get('reviewer'), str) or not output['reviewer'].strip():
                raise ValueError(f"Missing reviewer: {expected['id']}")
            for stage in ('raw', 'guarded'):
                label = output.get('labels', {}).get(stage, {})
                faithful, relevance = label.get('faithful'), label.get('relevance')
                if type(faithful) is not bool or type(relevance) is not int or not 0 <= relevance <= 3:
                    raise ValueError(f"Incomplete or invalid {stage} labels: {expected['id']}")
                if output[stage] is None and (faithful or relevance != 0):
                    raise ValueError(f"Missing {stage} output must score false and zero: {expected['id']}")
                totals[model][stage].update(n=1, faithful=int(faithful), relevant=int(relevance >= 2),
                                            relevance_points=relevance)

    def score(counts):
        return {'n': counts['n'], 'faithfulness_rate': counts['faithful'] / counts['n'],
                'relevance_at_least_2_rate': counts['relevant'] / counts['n'],
                'mean_relevance_0_to_3': counts['relevance_points'] / counts['n']}

    metrics = {model: {stage: score(counts) for stage, counts in stages.items()}
               for model, stages in totals.items()}
    delta = {stage: {metric: metrics['finetuned'][stage][metric] - metrics['base'][stage][metric]
                     for metric in ('faithfulness_rate', 'relevance_at_least_2_rate', 'mean_relevance_0_to_3')}
             for stage in ('raw', 'guarded')}
    return {'scope': 'Human-reviewed fixed-context answer quality; not end-to-end retrieval quality.',
            'evaluation_sha256': sha(dataset), 'base_model': comparison['base_model'],
            'finetuned_model': comparison['finetuned_model'], 'metrics': metrics,
            'finetuned_minus_base': delta}


def memory_report(dataset, comparison):
    validate_comparison(dataset, comparison)
    details = []
    for case, row in zip(dataset['cases'], comparison['paired']):
        if case['id'] != row['id'] or 'expected_movie_ids' not in case or 'expected_status' not in case:
            raise ValueError('Memory cases need aligned expected IDs and status')
        scores = {}
        for model in ('base', 'finetuned'):
            run = row[model]
            raw_ok = False
            if run.get('generations'):
                try:
                    answer = RAGAnswer.model_validate(json.loads(run['generations'][0]['raw']))
                    raw_ok = (answer.status == case['expected_status'] and
                              [movie.movie_id for movie in answer.movies] == case['expected_movie_ids'] and
                              run['generations'][0]['checks']['source_identity'])
                except (ValueError, TypeError, KeyError):
                    pass
            guarded = run.get('guarded_response')
            scores[model] = {'raw': raw_ok,
                             'guarded': bool(guarded and guarded['status'] == case['expected_status'] and
                                             [m['movie_id'] for m in guarded['movies']] == case['expected_movie_ids'])}
        details.append({'id': case['id'], 'expected_movie_ids': case['expected_movie_ids'], **scores})
    return {'scope': dataset.get('scope'), 'evaluation_sha256': sha(dataset),
            'cases': len(details), 'success_rate': {
                model: {stage: sum(row[model][stage] for row in details) / len(details)
                        for stage in ('raw', 'guarded')} for model in ('base', 'finetuned')},
            'details': details}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('filters', 'review-template', 'review-score', 'memory-score'):
        command = sub.add_parser(name)
        command.add_argument('--output', type=Path, required=True)
        command.add_argument('--evaluation', type=Path, required=True)
        if name != 'filters':
            command.add_argument('--comparison', type=Path, required=True)
        if name == 'review-score':
            command.add_argument('--review', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve evaluation evidence')
    dataset = json.loads(args.evaluation.read_text(encoding='utf-8'))
    if args.command == 'filters':
        result = filter_report(dataset)
    else:
        comparison = json.loads(args.comparison.read_text(encoding='utf-8'))
        if args.command == 'review-template':
            result = review_template(dataset, comparison)
        elif args.command == 'review-score':
            review = json.loads(args.review.read_text(encoding='utf-8'))
            result = review_report(dataset, comparison, review)
        else:
            result = memory_report(dataset, comparison)
    save_new(args.output, result)


if __name__ == '__main__':
    main()
