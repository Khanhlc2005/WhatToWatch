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
