import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('evaluate_retrieval', SCRIPTS / 'evaluate_retrieval.py')
evaluation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluation)


def movie():
    return dict(movie_id=1, imdb_id='tt1', tmdb_id=2, title='Example', overview='Context',
                genres=[{'name':'Drama'}], production_countries=[{'iso_3166_1':'US'}],
                release_date='2000-01-01', original_language='en', imdb_rating=8, runtime_minutes=90)


def test_filter_boundaries_and_missing_values():
    m = movie()
    assert evaluation.matches(m, dict(year_min=2000,year_max=2000,rating_min=8,runtime_max=90,genres=['Drama'],countries=['US'],languages=['en']))
    for f in [dict(year_min=2001),dict(year_max=1999),dict(rating_min=9),dict(runtime_max=89),dict(exclude_genres=['Drama']),dict(languages=['ja']),dict(countries=['JP']),dict(genres=['Horror'])]:
        assert not evaluation.matches(m,f)
    m['runtime_minutes']=None
    assert not evaluation.matches(m,dict(runtime_max=90))


def test_identity_duplicate_score_and_filter_checks():
    hit=dict(movie_id=1,imdb_id='tt1',tmdb_id=2,score=.8)
    assert evaluation.check_hits([hit],{1:movie()}, {}) == []
    assert 'duplicate_id' in evaluation.check_hits([hit,hit],{1:movie()}, {})
    assert 'identity_mismatch' in evaluation.check_hits([dict(hit,tmdb_id=3)],{1:movie()}, {})
    assert 'unverified_id' in evaluation.check_hits([dict(hit,movie_id=True)],{1:movie()}, {})
    assert 'invalid_score' in evaluation.check_hits([dict(hit,score=float('nan'))],{1:movie()}, {})
    assert 'score_order' in evaluation.check_hits([hit,dict(hit,score=.9)],{1:movie()}, {})
    assert 'filter_violation' in evaluation.check_hits([hit],{1:movie()}, {'year_min':2001})


def test_export_pools_modes_without_creating_judgments(tmp_path):
    import csv
    runs=[dict(query_id='Q1',query='example',filters={},mode=mode,response={'hits':[dict(movie_id=1,title='Example',score=.8)]}) for mode in evaluation.MODES]
    evaluation.export_tables(runs,{1:movie()},tmp_path)
    with (tmp_path/'manual_evaluation.csv').open(encoding='utf-8-sig') as f: rows=list(csv.DictReader(f))
    assert len(rows)==1
    assert rows[0]['relevance']==rows[0]['reviewer']==''
    assert all(rows[0][mode+'_rank']=='1' for mode in evaluation.MODES)


def test_reranker_mixed_score_domains_do_not_report_false_order_error():
    hit = dict(movie_id=1, imdb_id='tt1', tmdb_id=2, score=-2, retrieval_score=.8, rerank_score=-2)
    fallback = dict(movie_id=2, imdb_id='tt2', tmdb_id=3, score=.9, retrieval_score=.9)
    catalog = {1:movie(), 2:dict(movie(),movie_id=2,imdb_id='tt2',tmdb_id=3)}
    assert evaluation.check_hits([hit,fallback], catalog, {}, rerank=True) == []
    assert 'rerank_after_unscored' in evaluation.check_hits([fallback,hit], catalog, {}, rerank=True)


def test_metrics_require_complete_labels_and_skip_failed_queries():
    run = dict(query_id='Q1', mode='dense', issues=[], response={'hits':[{'movie_id':1},{'movie_id':2}]})
    assert not evaluation.quality_metrics([run], {}, 2)['results']
    assert not evaluation.quality_metrics([run], {('Q1',1):3}, 2)['results']
    # Mathematical fixtures only; these labels are never written into evaluation artifacts.
    result = evaluation.quality_metrics([run], {('Q1',1):3,('Q1',2):0}, 2)['results'][0]
    assert result['precision_at_k'] == .5 and result['mrr_at_k'] == result['ndcg_at_k'] == 1
    assert not evaluation.quality_metrics([dict(run,issues=['duplicate_id'])], {('Q1',1):3,('Q1',2):0}, 2)['results']


def test_labels_reject_unattributed_invalid_and_duplicate_judgments(tmp_path):
    import pytest
    path = tmp_path / 'labels.csv'
    for body in ['Q1,1,3,', 'Q1,1,4,reviewer', 'Q2,1,3,reviewer', 'Q1,1,3,reviewer\nQ1,1,3,reviewer']:
        path.write_text('query_id,movie_id,relevance,reviewer\n' + body + '\n')
        with pytest.raises(ValueError): evaluation.load_labels(path, {'Q1'}, {1:movie()})
    path.write_text('query_id,movie_id,relevance,reviewer\nQ1,1,,\n')
    assert evaluation.load_labels(path, {'Q1'}, {1:movie()}) == {}


def test_export_preserves_malformed_score_for_review(tmp_path):
    runs = [dict(query_id='Q1',query='example',filters={},mode='hybrid_reranker',response={'hits':[dict(movie_id=1,score=None)]})]
    evaluation.export_tables(runs, {1:movie()}, tmp_path)
    assert (tmp_path / 'manual_evaluation.csv').exists()


def test_runner_sends_four_variants_and_never_derives_labels_from_anchors(tmp_path, monkeypatch):
    import io
    import json
    queries = tmp_path / 'queries.json'
    queries.write_text(json.dumps({'limit':1,'queries':[dict(id='Q1',query='example',filters={},
        expected_movie_ids=[],relevance_status='unjudged',catalog_anchors=[dict(movie_id=1,imdb_id='tt1',tmdb_id=2,title='Example')])]}))
    movies = tmp_path / 'movies.jsonl'
    movies.write_text(json.dumps(movie()) + '\n')
    csv_path = tmp_path / 'movies.csv'
    csv_path.write_text('id,imdb_id,tmdb_id\n1,tt1,2\n')
    output = tmp_path / 'runs'
    calls = []
    def respond(request, timeout):
        body = json.loads(request.data)
        calls.append(body)
        hit = dict(movie_id=1,imdb_id='tt1',tmdb_id=2,title='Example',score=.8)
        if body.get('rerank'): hit.update(retrieval_score=.01,rerank_score=.8)
        return io.BytesIO(json.dumps(dict(mode=body['mode'],hits=[hit])).encode())
    monkeypatch.setattr(evaluation.urllib.request,'urlopen',respond)
    monkeypatch.setattr(sys,'argv',['evaluate_retrieval','--queries',str(queries),'--movies',str(movies),
        '--mysql-csv',str(csv_path),'--output',str(output),'--modes',*evaluation.MODES,'--candidate-k','7'])
    assert evaluation.main() == 0
    assert [c['mode'] for c in calls] == ['dense','sparse','hybrid','hybrid']
    assert calls[-1]['rerank'] is True and calls[-1]['candidate_k'] == 7
    assert not json.loads((output/'quality_metrics.json').read_text())['results']
    assert json.loads((output/'summary.json').read_text())['failed_checks'] == 0


def test_review_labels_are_bound_to_question_and_filters(tmp_path):
    import csv
    import pytest
    path = tmp_path / 'labels.csv'
    with path.open('w') as stream:
        writer=csv.DictWriter(stream,fieldnames=['query_id','movie_id','relevance','reviewer','query','filters'])
        writer.writeheader(); writer.writerow(dict(query_id='Q1',movie_id=1,relevance=1,reviewer='fixture',query='changed',filters='{}'))
    with pytest.raises(ValueError,match='query/filter mismatch'):
        evaluation.load_labels(path, {'Q1'}, {1:movie()}, {'Q1':dict(query='original',filters={})})


def test_malformed_http_response_cannot_break_evidence_export(tmp_path):
    runs = [dict(query_id='Q1',query='example',filters={},mode='dense',issues=['request_failed'],
        response=response) for response in [None, [], {'hits':None}, {'hits':[None,{'movie_id':[]}]}]]
    evaluation.export_tables(runs,{1:movie()},tmp_path)
    assert evaluation.quality_metrics(runs,{},10)['skipped']['Q1'] == 'structural/request failure'
