import json

import pytest

from finetuning.scripts.build_sft_v1 import build
from finetuning.scripts.validate_sft_v1 import validate


@pytest.fixture
def dataset(tmp_path):
    source = tmp_path / 'movies.jsonl'
    source.write_text(''.join(json.dumps(dict(movie_id=i, title=f'Movie {i}', genres=[{'name':'Drama'}],
        directors=[{'name':f'Director {i}'}], imdb_id=f'tt{i}', tmdb_id=i)) + '\n' for i in range(1, 31)))
    output = tmp_path / 'dataset'
    build(source, output, 30, 'en')
    return source, output


def test_english_dataset_matches_runtime_and_passes_integrity(dataset):
    from app.services.rag import SYSTEM_PROMPT
    source, output = dataset
    report = validate(source, output)
    assert report['passed'] and report['training_ready']
    row = json.loads((output / 'train.jsonl').read_text().splitlines()[0])
    assert row['messages'][0]['content'] == SYSTEM_PROMPT
    assert 'CONVERSATION_HISTORY' in row['messages'][1]['content']
    assert json.loads(row['messages'][2]['content'])['answer'].startswith(('The director', 'The movie'))


def test_validator_rejects_corrupted_target_and_provenance(dataset):
    source, output = dataset
    path = output / 'train.jsonl'
    rows = path.read_text().splitlines()
    row = json.loads(rows[0])
    row['messages'][2]['content'] = '{"status":"answered","answer":"Invented facts here","movies":[{"movie_id":"9999","title":"Wrong","reason":"Wrong"}]}'
    row['provenance']['source_sha256'] = 'wrong'
    rows[0] = json.dumps(row)
    path.write_text('\n'.join(rows) + '\n')
    report = validate(source, output)
    assert not report['passed']
    assert any('invalid provenance' in i for i in report['issues'])
    assert 'generator/source mismatch: train.jsonl' in report['issues']


def test_validator_detects_duplicate_and_cross_split_identity(dataset):
    source, output = dataset
    train = output / 'train.jsonl'
    row = train.read_text().splitlines()[0]
    with train.open('a') as stream: stream.write(row + '\n')
    with (output / 'test.jsonl').open('a') as stream: stream.write(row + '\n')
    report = validate(source, output)
    assert not report['passed']
    assert any('duplicate example' in i for i in report['issues'])
    assert any('wrong deterministic split' in i for i in report['issues'])


def test_english_generator_handles_genre_only_movie(tmp_path):
    source = tmp_path / 'movies.jsonl'
    source.write_text(json.dumps(dict(movie_id=1,title='Example',genres=[{'name':'Drama'}])) + '\n')
    output = tmp_path / 'dataset'
    manifest = build(source, output, 1, 'en')
    assert sum(manifest['examples'].values()) == 1
    assert validate(source, output)['passed']
