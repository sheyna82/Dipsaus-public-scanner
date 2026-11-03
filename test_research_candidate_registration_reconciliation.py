import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from research_immutable_candidate_registration import register_candidate_once
from research_candidate_registration_reconciliation import reconcile_candidate_records


class ReconciliationTests(unittest.TestCase):
    def candidate(self):
        return {"symbol": "AMD", "signal_session": "2026-11-02",
                "protocol_id": "v1", "future_outcome": None, "trade_ready": False}

    def test_cross_directory_same_candidate_conflict(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a", Path(tmp) / "b"
            a.mkdir()
            b.mkdir()
            first = register_candidate_once(self.candidate(), a,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            second = register_candidate_once(self.candidate(), b,
                clock=lambda: datetime(2026, 11, 3, 16, tzinfo=timezone.utc))
            with self.assertRaisesRegex(ValueError, "cross_run_candidate_registration_conflict"):
                reconcile_candidate_records([first["path"], second["path"]])

    def test_same_bytes_are_deduplicated(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = register_candidate_once(self.candidate(), tmp,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            report = reconcile_candidate_records([result["path"], result["path"]])
            self.assertEqual(report["candidate_count"], 1)
            self.assertFalse(report["collection_complete_independently"])
            self.assertFalse(report["trade_ready"])

    def test_distinct_symbols_are_retained(self):
        with tempfile.TemporaryDirectory() as tmp:
            first = register_candidate_once(self.candidate(), tmp,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            second = register_candidate_once(dict(self.candidate(), symbol="COHU"), tmp,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            report = reconcile_candidate_records([first["path"], second["path"]])
            self.assertEqual(report["candidate_count"], 2)


if __name__ == "__main__":
    unittest.main()
