"""Offline US capture integration regression."""
import tempfile
import unittest
from pathlib import Path
from research.candidate_us_offline_capture import build_records, archive_capture


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
            with self.assertRaisesRegex(ValueError, "FAILURES_REQUIRE_COMPLETE_CAPTURE_ARCHIVE"):
                archive_capture(item, Path(directory))
            self.assertFalse(list(Path(directory).iterdir()))

    def test_conflicting_outcomes_blocked(self):
        item = capture()
        item["failures"]["AAA"] = "TimeoutError"
        with self.assertRaisesRegex(ValueError, "CONFLICTING_OUTCOMES"):
            build_records(item)


if __name__ == "__main__":
    unittest.main()
