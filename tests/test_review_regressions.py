from contextlib import closing
import sqlite3
import tempfile
import unittest
from pathlib import Path

from indian_market_core.calendar import check, load, sessions
from indian_trader import costs, paper, validation


class ReviewRegressions(unittest.TestCase):
    def test_windows_reject_overlap_including_closed_final(self):
        with self.assertRaisesRegex(ValueError, 'nonoverlapping'):
            validation.evaluate([], {}, ('2024-01-01', '2024-06-30'),
                                ('2024-06-01', '2024-12-31'))
        with self.assertRaises(ValueError):
            validation.evaluate([], {}, ('2024-01-01', '2024-02-01'),
                                ('2024-03-01', '2024-04-01'), ('2024-03-15', '2024-05-01'))

    def test_fees_reject_unknown_history_and_invalid_values(self):
        for day in ('2000-01-01', '2027-01-01', 'not-a-date'):
            with self.assertRaises(ValueError):
                costs.leg('delivery', day, 'buy', 100)
        for value in (-1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                costs.leg('delivery', '2024-01-01', 'buy', value)
        self.assertEqual(costs.leg('delivery', '2024-01-01', 'buy', 0)['total'], 0)

    def test_incomplete_marks_and_sub_paise(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'paper.db'
            paper.initialize(p, 10000)
            paper.fill(p, 'one', 'A', 'buy', 1, 100, fee=0)
            result = paper.status(p, {})
            self.assertIsNone(result['equity'])
            self.assertFalse(result['valuation_complete'])
            self.assertEqual(result['known_value_subtotal'], 9900)
            with self.assertRaises(ValueError):
                paper.fill(p, 'two', 'A', 'buy', 1, .001, fee=0)

    def test_future_ledger_schema_not_modified(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'paper.db'
            with closing(sqlite3.connect(p)) as c:
                c.execute('PRAGMA user_version=99')
            with self.assertRaises(ValueError):
                paper.status(p)
            with closing(sqlite3.connect(p)) as c:
                self.assertEqual(c.execute('PRAGMA user_version').fetchone()[0], 99)

    def test_calendar_uses_exchange_date_and_bounded_coverage(self):
        result = check([{'timestamp': '2026-01-04T18:30:00+00:00', 'symbol': 'A'}], load())
        self.assertEqual(result['symbols']['A']['first'], '2026-01-05')
        with self.assertRaises(ValueError):
            sessions('2024-01-01', '2024-01-10')

    def test_invalid_resampling_budget(self):
        with self.assertRaises(ValueError):
            validation.null_runs([], {}, '2024-01-01', '2024-12-31', seeds=0)
        with self.assertRaises(ValueError):
            validation.sweep([], {}, {'fast': [5]}, ('2024-01-01', '2024-12-31'), block=0)
