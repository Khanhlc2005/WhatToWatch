import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


quality = load('evaluate_chat_quality')
chatbot = load('evaluate_chatbot')


def test_filter_f1_counts_false_positives_and_omissions():
    dataset = {'cases': [
        {'id': 'one', 'message': 'Recommend an action movie',
         'expected': {'retrieval': {'genres': ['Action', 'Comedy']}}},
        {'id': 'two', 'message': 'Who directed this movie?', 'expected': {}},
    ]}
    report = quality.filter_report(dataset)
    assert report['micro'] == {'tp': 1, 'fp': 0, 'fn': 1,
                               'precision': 1.0, 'recall': 0.5, 'f1': 2 / 3}
    assert report['exact_match_rate'] == 0.5
    assert report['details'][0]['fn'] == [['genres', 'comedy']]


def test_curated_filter_regression_set_has_no_mismatches():
    dataset = json.loads((ROOT / 'evaluation/chat_filters_v1.json').read_text())
    report = quality.filter_report(dataset)
    assert report['cases'] == 12
    assert report['micro']['f1'] == 1.0
    assert report['exact_match_rate'] == 1.0


def test_capture_passes_history_and_scores_memory_id(monkeypatch):
    import io

    first = {'id': 'M01', 'question': 'Who directed that movie?',
             'context': [{'movie_id': '1', 'title': 'First', 'director': 'First Director'},
                         {'movie_id': '2', 'title': 'Second', 'director': 'Second Director'}],
             'history': [{'role': 'assistant', 'content': 'I recommend Second.', 'movie_ids': [2]}],
             'summary': 'The user asked for an animated movie.',
             'expected_status': 'answered', 'expected_movie_ids': ['2']}
    answer = {'status': 'answered', 'answer': 'Second Director directed it.',
              'movies': [{'movie_id': '2', 'title': 'Second', 'reason': 'Director: Second Director'}]}
    prompts = []

    def respond(request, timeout):
        if request.data is None:
            return io.BytesIO(b'{"models":[{"name":"fixture","digest":"a"}]}')
        body = json.loads(request.data)
        prompts.append(body['prompt'])
        return io.BytesIO(json.dumps({'response': json.dumps(answer)}).encode())

    monkeypatch.setattr(chatbot.urllib.request, 'urlopen', respond)
    run = chatbot.capture({'cases': [first]}, 'fixture', 'http://fixture')['runs'][0]
    assert run['memory_movie_ids_match'] is True
    assert run['structural_status_match'] is True
    assert 'I recommend Second.' in prompts[0]
    assert 'The user asked for an animated movie.' in prompts[0]


def paired_fixture():
    case = {'id': 'Q1', 'question': 'Recommend a movie',
            'context': [{'movie_id': '1', 'title': 'Example', 'genres': ['Drama']}]}
    dataset = {'cases': [case]}
    answer = {'status': 'answered', 'answer': 'This fits the request.',
              'movies': [{'movie_id': '1', 'title': 'Example', 'reason': 'Genres: Drama'}]}
    raw = json.dumps(answer)
    run = {'id': 'Q1', 'input_sha256': quality.sha(case),
           'generations': [{'raw': raw, 'checks': {'source_identity': True}}],
           'guarded_response': answer}
    comparison = {'evaluation_sha256': quality.sha(dataset),
                  'base_model': 'base', 'finetuned_model': 'tuned',
                  'base_model_digest': 'a', 'finetuned_model_digest': 'b',
                  'paired': [{'id': 'Q1', 'base': run, 'finetuned': run}]}
    return dataset, comparison


def test_review_requires_complete_labels_and_unchanged_outputs():
    dataset, comparison = paired_fixture()
    review = quality.review_template(dataset, comparison)
    with pytest.raises(ValueError, match='Missing reviewer'):
        quality.review_report(dataset, comparison, review)
    for output in review['cases'][0]['outputs']:
        output['reviewer'] = 'reviewer-1'
        for stage in ('raw', 'guarded'):
            output['labels'][stage] = {'faithful': output['slot'] == 'A',
                                       'relevance': 3 if output['slot'] == 'A' else 1}
    report = quality.review_report(dataset, comparison, review)
    assert report['metrics']['base']['raw']['n'] == 1
    assert abs(report['finetuned_minus_base']['raw']['faithfulness_rate']) == 1
    review['cases'][0]['outputs'][0]['raw'] = 'changed'
    with pytest.raises(ValueError, match='Review output changed'):
        quality.review_report(dataset, comparison, review)


def test_memory_report_requires_distinct_model_and_scores_raw_and_guarded():
    dataset, comparison = paired_fixture()
    dataset['cases'][0].update(expected_status='answered', expected_movie_ids=['1'])
    comparison['evaluation_sha256'] = quality.sha(dataset)
    for model in ('base', 'finetuned'):
        comparison['paired'][0][model]['input_sha256'] = quality.sha(dataset['cases'][0])
    report = quality.memory_report(dataset, comparison)
    assert report['success_rate']['base'] == {'raw': 1.0, 'guarded': 1.0}
    comparison['finetuned_model_digest'] = comparison['base_model_digest']
    with pytest.raises(ValueError, match='same model'):
        quality.memory_report(dataset, comparison)
