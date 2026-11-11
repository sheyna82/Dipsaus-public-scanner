"""Offline US capture integration regression."""
import json
import tempfile
import unittest
from pathlib import Path
from research.candidate_us_offline_capture import build_records, archive_capture
from research.candidate_us_decision_archive import verify_decision_archive


def assessment():
    return {"last_bar_date": "2026-11-02", "drawdown_pct": -10,
            "rebound_from_low_pct": 4, "early_turn": False,
            "established_turn": False, "signal_count": 1,
            "signals": {"positive_2d_change": True}, "pre_screen_match": False}


def capture():
    return {"sample_symbols": ["AAA"], "assessments": {"AAA": assessment()},
            "failures": {}, "observed_at_utc": "2026-11-03T12:00:00Z"}


class OfflineCaptureTests(unittest.TestCase):
    def test_archive_complete_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            result = archive_capture(capture(), Path(directory))
            self.assertEqual(result["requested_count"], 1)
            self.assertEqual(result["assessed_count"], 1)
            self.assertTrue(Path(result["archive"]["path"]).is_file())
            self.assertFalse(result["prospective_capture_independently_verified"])
            verified = verify_decision_archive(result["archive"]["path"], result["archive"]["sha256"])
            self.assertEqual(verified["requested_count"], 1)
            self.assertTrue(verified["screening_complete"])

    def test_missing_rejection_is_blocked(self):
        item = capture()
        item["sample_symbols"].append("BBB")
        with self.assertRaisesRegex(ValueError, "INCOMPLETE_OR_FOREIGN_SYMBOLS"):
            build_records(item)

    def test_failures_are_not_silently_omitted_from_archive(self):
        item = capture()
        item["sample_symbols"].append("BBB")
        item["failures"]["BBB"] = "TimeoutError"
        with tempfile.TemporaryDirectory() as directory:
            result = archive_capture(item, Path(directory))
            archived = json.loads(Path(result["archive"]["path"]).read_text())
            self.assertEqual(archived["failed_symbols"], {"BBB": "TimeoutError"})
            self.assertEqual(archived["requested_count"], 2)
            self.assertEqual(archived["record_count"], 1)
            self.assertFalse(archived["screening_complete"])
            self.assertFalse(archived["trade_ready"])
            verified = verify_decision_archive(result["archive"]["path"], result["archive"]["sha256"])
            self.assertEqual(verified["failure_count"], 1)
            self.assertFalse(verified["screening_complete"])

    def test_all_failed_requests_still_archived(self):
        item = capture()
        item["assessments"] = {}
        item["failures"] = {"AAA": "TimeoutError"}
        with tempfile.TemporaryDirectory() as directory:
            result = archive_capture(item, Path(directory))
            archived = json.loads(Path(result["archive"]["path"]).read_text())
            self.assertEqual(archived["record_count"], 0)
            self.assertEqual(archived["failure_count"], 1)
            self.assertFalse(archived["screening_complete"])

    def test_readback_rejects_tampered_archive(self):
        item = capture()
        with tempfile.TemporaryDirectory() as directory:
            result = archive_capture(item, Path(directory))
            path = Path(result["archive"]["path"])
            path.write_bytes(path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "ARCHIVE_HASH_MISMATCH"):
                verify_decision_archive(path, result["archive"]["sha256"])

    def test_conflicting_outcomes_blocked(self):
        item = capture()
        item["failures"]["AAA"] = "TimeoutError"
        with self.assertRaisesRegex(ValueError, "CONFLICTING_OUTCOMES"):
            build_records(item)


if __name__ == "__main__":
    unittest.main()
