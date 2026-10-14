import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('evaluate_chatbot', Path(__file__).resolve().parents[1] / 'scripts/evaluate_chatbot.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def test_compare_requires_identical_set_prompt_options_and_ids():
    dataset = {'cases':[{'id':'Q1','question':'question','context':[]}]}
    capture = dict(model='fixture',evaluation_sha256=evaluation.sha(dataset),
        system_prompt_sha256=evaluation.sha(evaluation.SYSTEM_PROMPT),generation_options={},
        runs=[dict(id='Q1',input_sha256=evaluation.sha(dataset['cases'][0]),error='fixture error')])
    assert evaluation.compare(dataset,capture,capture)['quality_metrics'] is None
    for changed in [dict(evaluation_sha256='wrong'),dict(system_prompt_sha256='wrong'),dict(generation_options={'temperature':1}),dict(runs=[]),dict(runs=capture['runs'] * 2)]:
        with pytest.raises(ValueError): evaluation.compare(dataset,capture,dict(capture,**changed))


def test_raw_contract_and_identity_are_independent_checks():
    import json
    from app.schemas.rag import MovieContext
    context = [MovieContext(movie_id='1',title='Example',genres=['Drama'])]
    raw = dict(status='answered',answer='A sufficiently long answer.',movies=[dict(movie_id='1',title='Example',reason='Genres: Drama')])
    assert evaluation.checks(json.dumps(raw),context) == dict(json_contract=True,source_identity=True,reason_fact_support=True)
    raw['movies'][0]['movie_id'] = '2'
    checks = evaluation.checks(json.dumps(raw),context)
    assert checks['json_contract'] and not checks['source_identity']
    assert not evaluation.checks('not json',context)['json_contract']


def test_prepare_rejects_training_overlap(tmp_path):
    import json
    train = tmp_path / 'train.jsonl'
    train.write_text(json.dumps({'provenance':{'source_movie_id':1}}) + '\n')
    queries = {'queries':[dict(id='Q1',query='Example',catalog_anchors=[{'movie_id':1}])]}
    with pytest.raises(ValueError,match='overlaps SFT train'): evaluation.prepare(queries,{1:{}},train)


def test_capture_does_not_pull_uninstalled_model(monkeypatch):
    import io
    monkeypatch.setattr(evaluation.urllib.request,'urlopen',lambda *args,**kwargs: io.BytesIO(b'{"models":[]}'))
    with pytest.raises(ValueError,match='already be installed'): evaluation.capture({'cases':[]},'absent','http://fixture')


def test_capture_records_raw_and_guarded_responses_on_same_inputs(monkeypatch):
    import io
    import json
    dataset = {'cases':[dict(id='Q1',question='Who directed this movie?',context=[dict(movie_id='1',title='Example',director='Example Director')]) ]}
    calls = []
    raw = dict(status='answered',answer='The director is Example Director.',movies=[dict(movie_id='1',title='Example',reason='Director: Example Director')])
    def respond(request, timeout):
        if request.data is None: return io.BytesIO(b'{"models":[{"name":"fixture","digest":"abc"}]}')
        calls.append(json.loads(request.data))
        return io.BytesIO(json.dumps({'response':json.dumps(raw)}).encode())
    monkeypatch.setattr(evaluation.urllib.request,'urlopen',respond)
    result = evaluation.capture(dataset,'fixture','http://fixture')
    assert len(calls) == 1
    assert calls[0]['system'] == evaluation.SYSTEM_PROMPT
    assert calls[0]['options']['temperature'] == 0
    assert result['runs'][0]['generations'][0]['checks']['source_identity']
    assert result['runs'][0]['guarded_response']['answer'] == 'Example Director'
    assert result['model_digest'] == 'abc'
