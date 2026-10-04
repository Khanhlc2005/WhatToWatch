"""Offline reliability tests; fake API responses are never catalog evidence."""
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from full_catalog import Client, FetchError, NetworkStopped, atomic_json, export, init_state, run, network_error_kind
from validate_catalog import validate


def imdb(identifier):
    return dict(tconst=identifier, titleType='movie', primaryTitle='Test', startYear='2001',
                averageRating=7.1, numVotes=50, genres='Drama', isAdult='0', runtimeMinutes='90')


def details(identifier, number):
    return dict(id=number, imdb_id=identifier, title='Test', genres=[],
                credits=dict(cast=[], crew=[]), keywords=dict(keywords=[]), videos=dict(results=[]))


class FakeClient:
    requests = 0

    def get(self, endpoint, **params):
        self.requests += 1
        if endpoint.startswith('find/'):
            return {'movie_results': [{'id': int(endpoint.split('tt')[1])}]}
        number = int(endpoint.split('/')[1])
        return details(f'tt{number:07d}', number)


class FullCatalogTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.db = sqlite3.connect(self.folder / 'state.sqlite')
        self.addCleanup(self.db.close)
        self.db.executescript('''
          CREATE TABLE catalog (imdb_id TEXT PRIMARY KEY, imdb_json TEXT, tmdb_id INTEGER, mapping_source TEXT);
          CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT);
        ''')
        init_state(self.db)

    def add(self, number, mapped=None):
        identifier = f'tt{number:07d}'
        self.db.execute('INSERT INTO catalog VALUES (?,?,?,NULL)',
                        (identifier, json.dumps(imdb(identifier)), mapped))
        self.db.commit()

    def test_resume_and_repeat_export_without_duplicates(self):
        for number in range(1, 26):
            self.add(number, number if number % 2 else None)
        client = FakeClient()
        self.assertEqual(run(self.db, self.folder, client, limit=7)['succeeded'], 7)
        self.assertEqual(run(self.db, self.folder, client)['succeeded'], 18)
        previous_requests = client.requests
        self.assertEqual(run(self.db, self.folder, client)['already_completed'], 25)
        self.assertEqual(client.requests, previous_requests)
        self.db.execute('INSERT INTO metadata VALUES (?,?)', ('inventory', json.dumps(
            dict(eligible_imdb_rows=25, input_rows=25, run_started_at='test', source_file_versions={}))))
        report = export(self.db, self.folder / 'export')
        path = self.folder / 'export/movies_cleaned_full.jsonl'
        first = path.read_bytes()
        export(self.db, self.folder / 'export')
        self.assertEqual(first, path.read_bytes())
        self.assertEqual(report['output_rows'], 25)
        self.assertTrue(report['complete'])
        self.assertEqual(report['missing_by_field']['trailer'], 25)

    def test_raw_cache_survives_crash_before_checkpoint(self):
        self.add(1, 1)
        client = FakeClient()
        with patch('full_catalog.transform', side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                run(self.db, self.folder, client)
        self.assertTrue((self.folder / 'movie/1.json').exists())
        self.assertEqual(self.db.execute('SELECT count(*) FROM results').fetchone()[0], 0)
        result = run(self.db, self.folder)
        self.assertEqual(result['skipped_from_cache'], 1)
        self.assertEqual(result['succeeded'], 1)

    def test_conflicting_tmdb_does_not_delete_success(self):
        self.add(1, 1)
        self.add(2, 1)
        run(self.db, self.folder, FakeClient(), limit=1)
        # Simulate inconsistent external IDs in a replacement response.
        atomic_json(self.folder / 'movie/1.json', details('tt0000002', 1))
        self.assertEqual(run(self.db, self.folder)['failed'], 1)
        rows = self.db.execute('SELECT imdb_id, status, reason FROM results ORDER BY imdb_id').fetchall()
        self.assertEqual(rows, [('tt0000001', 'succeeded', None),
                                ('tt0000002', 'failed', 'duplicate_tmdb_id')])

    def test_wrong_id_fails_and_other_movie_continues(self):
        self.add(1, 1)
        self.add(2, 2)
        atomic_json(self.folder / 'movie/1.json', details('tt9999999', 1))
        result = run(self.db, self.folder, FakeClient())
        self.assertEqual((result['failed'], result['succeeded']), (1, 1))
        atomic_json(self.folder / 'movie/1.json', details('tt0000001', 1))
        self.assertEqual(run(self.db, self.folder, retry_failed=True)['succeeded'], 1)

    def test_offline_default_does_not_mark_missing_cache_complete(self):
        self.add(1)
        self.assertEqual(run(self.db, self.folder)['pending'], 1)
        self.assertEqual(self.db.execute('SELECT count(*) FROM results').fetchone()[0], 0)

    def test_find_empty_is_cached_but_ambiguous_is_failure(self):
        self.add(1)
        self.add(2)
        atomic_json(self.folder / 'find/tt0000001.json', {'movie_results': []})
        atomic_json(self.folder / 'find/tt0000002.json', {'movie_results': [{'id': 2}, {'id': 3}]})
        result = run(self.db, self.folder)
        self.assertEqual((result['unmatched'], result['failed']), (1, 1))

    def test_network_failure_stops_batch_after_checkpoint(self):
        self.add(1, 1)
        self.add(2, 2)
        client = FakeClient()
        client.get = lambda *a, **k: (_ for _ in ()).throw(NetworkStopped('network_retries_exhausted'))
        with self.assertRaises(NetworkStopped):
            run(self.db, self.folder, client)
        self.assertEqual(self.db.execute('SELECT count(*) FROM results').fetchone()[0], 1)

    def test_retry_after_and_secret_safe_network_exception(self):
        import requests
        from unittest.mock import Mock
        client = Client.__new__(Client)
        client.key, client.rate, client.attempts, client.last, client.requests = 'secret', 2, 3, 0, 0
        client.session = Mock()
        throttled = Mock(status_code=429, headers={'Retry-After': '7'})
        success = Mock(status_code=200)
        success.json.return_value = {'ok': True}
        client.session.get.side_effect = [throttled, success]
        with patch('full_catalog.time.sleep') as sleep:
            self.assertEqual(client.get('configuration'), {'ok': True})
            self.assertIn(((7.0,), {}), sleep.call_args_list)
        client.session.get.side_effect = requests.Timeout('URL contains secret')
        with patch('full_catalog.time.sleep'), self.assertRaisesRegex(NetworkStopped, '^network_retries_exhausted:request_error$'):
            client.get('configuration')

    def test_nested_reset_diagnosis_does_not_expose_credentials(self):
        import requests
        reset = ConnectionResetError(104, 'sensitive URL and token')
        wrapper = requests.ConnectionError('private URL', reset)
        self.assertEqual(network_error_kind(wrapper), 'connection_reset')

    def test_validator_checks_raw_cache_and_output_tampering(self):
        for number in range(1, 26):
            self.add(number, number)
        run(self.db, self.folder, FakeClient())
        self.db.execute('INSERT INTO metadata VALUES (?,?)', ('inventory', json.dumps(
            dict(eligible_imdb_rows=25, input_rows=25, run_started_at='test', source_file_versions={}))))
        self.db.commit()
        export(self.db, self.folder / 'export')
        output = self.folder / 'export/movies_cleaned_full.jsonl'
        sample = Path(__file__).resolve().parents[1] / 'seeds/movies_cleaned_sample.jsonl'
        args = (output, self.folder / 'state.sqlite', self.folder, sample)
        report = validate(*args)
        self.assertTrue(report['passed'], report['errors'])
        self.assertEqual(len(report['manual_review_sample']), 20)
        self.assertFalse(report['manual_review_completed'])
        self.assertEqual(report['missing_fraction_by_field']['trailer'], 1)
        complete = validate(*args, require_complete=True)
        self.assertFalse(complete['passed'])
        self.assertEqual(complete['errors']['required_reference_missing'], 3)
        lines = output.read_text().splitlines()
        movie = json.loads(lines[0])
        movie['embedding_text'] += '\nYear: 2001'
        lines[0] = json.dumps(movie)
        output.write_text('\n'.join(lines + [lines[1], '{broken']) + '\n')
        report = validate(*args)
        for reason in ('embedding_template_mismatch', 'checkpoint_mismatch',
                       'raw_cache_transform_mismatch', 'duplicate_imdb_id',
                       'duplicate_tmdb_id', 'invalid_json_object'):
            self.assertIn(reason, report['errors'])
        atomic_json(self.folder / 'movie/2.json', details('tt9999999', 2))
        self.assertIn('raw_cache_identity_or_structure_mismatch', validate(*args)['errors'])

    def test_validator_does_not_certify_missing_catalog_rows(self):
        self.add(1, 1)
        self.add(2, 2)
        run(self.db, self.folder, FakeClient(), limit=1)
        self.db.execute('INSERT INTO metadata VALUES (?,?)', ('inventory', json.dumps(
            dict(eligible_imdb_rows=2, input_rows=2, run_started_at='test', source_file_versions={}))))
        self.db.commit()
        export(self.db, self.folder / 'export')
        report = validate(self.folder / 'export/movies_cleaned_full.jsonl',
            self.folder / 'state.sqlite', self.folder,
            Path(__file__).resolve().parents[1] / 'seeds/movies_cleaned_sample.jsonl', True)
        self.assertFalse(report['passed'])
        self.assertIn('catalog_incomplete', report['errors'])

    def test_repeated_movie_server_error_does_not_stop_other_movies(self):
        from unittest.mock import Mock
        client = Client.__new__(Client)
        client.key, client.rate, client.attempts, client.last, client.requests = 'secret', 2, 3, 0, 0
        client.session = Mock()
        unavailable = Mock(status_code=503, headers={})
        success = Mock(status_code=200)
        success.json.return_value = details('tt0000002', 2)
        client.session.get.side_effect = [unavailable, unavailable, unavailable, success]
        self.add(1, 1)
        self.add(2, 2)
        with patch('full_catalog.time.sleep'), patch('builtins.print') as log:
            result = run(self.db, self.folder, client, progress_every=1)
        self.assertEqual((result['failed'], result['succeeded']), (1, 1))
        self.assertEqual(log.call_count, 2)
        first_progress = json.loads(log.call_args_list[0].args[0])
        self.assertEqual(first_progress['failed'], 1)
        self.assertEqual(first_progress['succeeded'], 0)


if __name__ == '__main__':
    unittest.main()
