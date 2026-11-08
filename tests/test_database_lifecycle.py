"""Retain connection references to catch leaks even on Unix before GC runs."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from indian_trader import bank, paper
from indian_trader.cli import demo


class DatabaseLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.connections = []
        original_connect = sqlite3.connect

        def tracked_connect(*args, **kwargs):
            con = original_connect(*args, **kwargs)
            self.connections.append(con)
            return con

        self.patcher = patch('sqlite3.connect', side_effect=tracked_connect)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        for con in self.connections:
            con.close()
        self.tmp.cleanup()

    def assert_closed(self):
        self.assertTrue(self.connections)
        for con in self.connections:
            with self.assertRaises(sqlite3.ProgrammingError):
                con.execute('SELECT 1')

    def test_bank_operations_close_connections(self):
        source = demo(self.root / 'demo.csv')
        bank.ingest(self.root / 'bank', 'demo', source, 'synthetic', 1000)
        self.assertEqual(len(bank.catalogue(self.root / 'bank')), 1)
        self.assertTrue(bank.verify(self.root / 'bank')[0]['ok'])
        self.assert_closed()

    def test_paper_success_and_failure_close_connections(self):
        path = self.root / 'paper.sqlite'
        paper.initialize(path, 1000)
        paper.fill(path, 'buy', 'DEMO', 'buy', 2, 100, 1)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            paper.fill(path, 'buy', 'DEMO', 'buy', 2, 100, 1)
        self.assertEqual(paper.status(path)['cash'], 799)
        self.assert_closed()

    def test_failed_transaction_rolls_back_before_close(self):
        path = self.root / 'paper.sqlite'
        paper.initialize(path, 1000)
        with self.assertRaisesRegex(RuntimeError, 'injected failure'):
            with paper.db(path) as con:
                con.execute('UPDATE account SET cash_paise=100 WHERE id=1')
                raise RuntimeError('injected failure')
        self.assertEqual(paper.status(path)['cash'], 1000)
        self.assert_closed()

    def test_schema_failure_closes_connection(self):
        path = self.root / 'invalid.sqlite'
        path.write_bytes(b'not a sqlite database')
        with self.assertRaises(sqlite3.DatabaseError):
            with paper.db(path):
                self.fail('invalid database must not yield a connection')
        self.assert_closed()
