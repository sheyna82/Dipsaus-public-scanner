"""Offline smoke tests for the research-only candidate snapshot."""
import importlib.util
import pathlib
import json
import hashlib
import tempfile
import unittest

MODULE_PATH = pathlib.Path(__file__).with_name("candidate_entry_snapshot.py")
spec = importlib.util.spec_from_file_location("candidate_entry_snapshot", MODULE_PATH)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)

class SnapshotTests(unittest.TestCase):
    def test_snapshot_archive_is_create_only_and_hash_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            record = {"generated_utc": "2026-11-04T10:00:00+00:00",
                      "research_only": True, "candidates": [{"symbol": "AMD", "decision": "WAIT"}]}
            archived = snapshot.archive_candidate_snapshot(record, pathlib.Path(tmp))
            self.assertEqual(hashlib.sha256(archived["path"].read_bytes()).hexdigest(),
                             archived["sha256"])
            self.assertEqual(json.loads(archived["path"].read_text()), record)
            with self.assertRaises(FileExistsError):
                snapshot.archive_candidate_snapshot(record, pathlib.Path(tmp))
            self.assertEqual(len(list(pathlib.Path(tmp).glob("*.json"))), 1)

    def test_rejects_unapproved_history_range(self):
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_HISTORY_RANGE"):
            snapshot.bars("AMD", history_range="max")

    def test_short_history_blocks(self):
        result = snapshot.analyze("BKD", [])
        self.assertFalse(result["trade_ready"])
        self.assertEqual(result["blocks"], ["INSUFFICIENT_DAILY_BARS"])

    def test_complete_history_stays_research_only(self):
        rows = [{"timestamp": 1700000000 + 86400*i, "close": 20 + i/100,
                 "high": 20.2 + i/100, "low": 19.8 + i/100,
                 "volume": 1000000} for i in range(120)]
        result = snapshot.analyze("COHU", rows)
        self.assertFalse(result["trade_ready"])
        self.assertEqual(result["decision"], "WAIT")
        self.assertEqual(set(result["historical_unconditional_windows"]), {"5", "10", "15"})
        self.assertIn("DEGIRO_BID_ASK_UNVERIFIED", result["blocks"])

if __name__ == "__main__":
    unittest.main()
