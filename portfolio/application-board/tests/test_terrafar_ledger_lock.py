"""Synthetic lock misuse checks; no real candidate state or network."""
import sys
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from terrafar_candidate_ledger import ledger_lock


class LedgerLockTests(unittest.TestCase):
    def test_same_thread_reentry_fails_before_wait_and_outer_lock_remains_usable(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            with ledger_lock(path):
                with patch('terrafar_candidate_ledger.fcntl.flock', side_effect=AssertionError('nested flock must not run')):
                    with self.assertRaisesRegex(RuntimeError, 'candidate_ledger_lock_reentry'):
                        with ledger_lock(path):
                            self.fail('reentry must not enter')
            with ledger_lock(path):
                pass

    def test_alias_path_cannot_hide_same_thread_reentry(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / 'alias').symlink_to(base, target_is_directory=True)
            with ledger_lock(base / 'ledger.json'):
                with patch('terrafar_candidate_ledger.fcntl.flock', side_effect=AssertionError('nested flock must not run')):
                    with self.assertRaisesRegex(RuntimeError, 'candidate_ledger_lock_reentry'):
                        with ledger_lock(base / 'alias' / 'ledger.json'):
                            self.fail('alias must not enter')

    def test_exception_releases_guard_and_file_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            with self.assertRaisesRegex(ValueError, 'interrupted'):
                with ledger_lock(path):
                    raise ValueError('interrupted')
            with ledger_lock(path):
                pass

    def test_ledger_file_symlink_cannot_create_a_second_lock_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            path = base / 'ledger.json'
            path.write_text('{}')
            alias = base / 'alias.json'
            alias.symlink_to(path)
            with ledger_lock(path):
                with self.assertRaisesRegex(ValueError, 'candidate_ledger_symlink_rejected'):
                    with ledger_lock(alias):
                        self.fail('ledger symlink must not enter')
            self.assertFalse((base / 'alias.json.lock').exists())

    def test_lock_file_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / 'other.lock'
            target.write_text('preserved')
            (base / 'ledger.json.lock').symlink_to(target)
            with self.assertRaisesRegex(ValueError, 'candidate_ledger_lock_symlink_rejected'):
                with ledger_lock(base / 'ledger.json'):
                    self.fail('lock symlink must not enter')
            self.assertEqual(target.read_text(), 'preserved')

    def test_distinct_ledgers_can_be_nested(self):
        with tempfile.TemporaryDirectory() as tmp:
            with ledger_lock(Path(tmp) / 'a.json'):
                with ledger_lock(Path(tmp) / 'b.json'):
                    pass

    def test_threads_still_serialize_instead_of_being_misidentified_as_reentry(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'ledger.json'
            entered = threading.Event()
            attempting = threading.Event()
            def acquire():
                attempting.set()
                with ledger_lock(path):
                    entered.set()
            with ThreadPoolExecutor(max_workers=1) as pool:
                with ledger_lock(path):
                    future = pool.submit(acquire)
                    self.assertTrue(attempting.wait(2))
                    self.assertFalse(entered.wait(0.02))
                future.result(timeout=2)
                self.assertTrue(entered.is_set())


if __name__ == '__main__':
    unittest.main()
