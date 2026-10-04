"""Offline tests for download limits, checkpoint preservation and streamed bodies."""
import json
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from full_catalog import BudgetStopped, init_state, run
from run_metered_catalog import Budget, MeteredSession


class MeteredTests(unittest.TestCase):
    def test_success_target_counts_checkpoint_and_ignores_unmatched(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('CREATE TABLE catalog (imdb_id TEXT, imdb_json TEXT, tmdb_id INTEGER)')
        for number in range(1, 5):
            imdb_id = f'tt{number:07d}'
            db.execute('INSERT INTO catalog VALUES (?,?,?)',
                       (imdb_id, json.dumps({'tconst': imdb_id}), number))
        init_state(db)
        db.execute("INSERT INTO results VALUES ('tt0000001',1,'succeeded',NULL,NULL,NULL,NULL)")

        def process(db, imdb, tmdb_id, cache, client):
            status = 'unmatched' if tmdb_id == 2 else 'succeeded'
            db.execute('INSERT INTO results VALUES (?,?,?,NULL,NULL,NULL,NULL)',
                       (imdb['tconst'], tmdb_id, status))
            db.commit()
            return status, False

        with patch('full_catalog.process_one', side_effect=process) as mocked:
            result = run(db, Path('/unused'), target_successes=2)
            self.assertEqual(result['succeeded'], 1)
            self.assertEqual(result['unmatched'], 1)
            self.assertEqual(mocked.call_count, 2)
            self.assertIsNone(db.execute("SELECT status FROM results WHERE imdb_id='tt0000004'").fetchone())
            mocked.reset_mock()
            run(db, Path('/unused'), target_successes=2)
            mocked.assert_not_called()

    def test_budget_persists_and_accounts_other_interface_traffic(self):
        with TemporaryDirectory() as directory, patch.object(Budget, 'counter', return_value=100) as counter:
            path = Path(directory) / 'usage.json'
            budget = Budget('wlo1', 10_000_000, path)
            budget.check(1000)
            counter.return_value = 2_000_100
            budget.check()
            resumed = Budget('wlo1', 10_000_000, path)
            self.assertEqual(resumed.state['interface_bytes'], 2_000_000)
            self.assertEqual(resumed.state['decoded_bytes'], 1000)
            counter.return_value = 5_000_100
            with self.assertRaises(BudgetStopped):
                resumed.check()
            self.assertEqual(json.loads(path.read_text())['interface_bytes'], 5_000_000)

    def test_budget_stop_keeps_movie_pending(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        db.execute('CREATE TABLE catalog (imdb_id TEXT, imdb_json TEXT, tmdb_id INTEGER)')
        db.execute('INSERT INTO catalog VALUES (?,?,?)',
                   ('tt0000001', json.dumps({'tconst': 'tt0000001'}), 1))
        client = Mock(requests=0)
        client.get.side_effect = BudgetStopped('data_budget_reached')
        with TemporaryDirectory() as directory, self.assertRaises(BudgetStopped):
            run(db, Path(directory), client)
        self.assertEqual(db.execute('SELECT count(*) FROM results').fetchone()[0], 0)

    def test_stream_abort_closes_response(self):
        budget = Mock(device='wlo1')
        budget.check.side_effect = [None, BudgetStopped('data_budget_reached')]
        response = Mock()
        response.iter_content.return_value = iter([b'first', b'second'])
        session = Mock()
        session.get.return_value = response
        with patch('run_metered_catalog.subprocess.check_output', return_value='uuid'), self.assertRaises(BudgetStopped):
            MeteredSession(session, budget, 'uuid').get('endpoint')
        response.close.assert_called_once()
        self.assertTrue(session.get.call_args.kwargs['stream'])

    def test_changed_network_prevents_request(self):
        session = Mock()
        budget = Mock(device='wlo1')
        with patch('run_metered_catalog.subprocess.check_output', return_value='different'), self.assertRaises(BudgetStopped):
            MeteredSession(session, budget, 'original').get('endpoint')
        session.get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
