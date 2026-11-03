"""Offline archive integration tests, without market requests or live scanner."""
import json
import tempfile
import unittest
from pathlib import Path
from research.candidate_us_decision_archive import archive_decision_batch
from research.candidate_us_decision_record import decision_record


def sample():
    return decision_record("ABC", {
        "last_bar_date": "2026-11-02", "drawdown_pct": -10,
        "rebound_from_low_pct": 4, "early_turn": False,
        "established_turn": False, "signal_count": 1,
        "signals": {"positive_2d_change": True}, "pre_screen_match": False,
    }, "2026-11-03T12:00:00Z")


class ArchiveTests(unittest.TestCase):
    def test_create_only_and_readback(self):
        with tempfile.TemporaryDirectory() as directory:
            result = archive_decision_batch([sample()], "2026-11-03T12:01:00Z", Path(directory))
            payload = json.loads(result["path"].read_text())
            self.assertEqual(payload["record_count"], 1)
            self.assertFalse(payload["prospective_capture_independently_verified"])
            with self.assertRaises(FileExistsError):
                archive_decision_batch([sample()], "2026-11-03T12:01:00Z", Path(directory))

    def test_tamper_fails_before_write(self):
        with tempfile.TemporaryDirectory() as directory:
            record = sample()
            record["features"]["drawdown_pct"] = -25
            with self.assertRaisesRegex(ValueError, "DECISION_RECORD_HASH_MISMATCH"):
                archive_decision_batch([record], "2026-11-03T12:01:00Z", Path(directory))
            self.assertFalse(list(Path(directory).iterdir()))

    def test_empty_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "EMPTY_DECISION_BATCH"):
            archive_decision_batch([], "2026-11-03T12:01:00Z")


if __name__ == "__main__":
    unittest.main()
