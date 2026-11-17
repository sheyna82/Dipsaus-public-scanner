"""Offline contract tests for OHLC swing evidence; no market-data requests."""
import unittest
from datetime import datetime, timezone, timedelta
from research.us_ohlc_structure_20261117 import swing_evidence


class SwingEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 9, tzinfo=timezone.utc)
        self.bars = [{"low": l, "high": h, "close": c} for l, h, c in [
            (10, 12, 11), (9, 13, 11), (8, 17, 12), (9, 14, 12),
            (10, 13, 11), (7, 12, 10), (9, 14, 12), (10, 13, 12),
            (11, 12, 11.5)]]

    def run_extractor(self, **kwargs):
        data = dict(bars=self.bars, dataset_id="ohlcv-sha256:test",
                    source="independent_history", timeframe="daily",
                    checked_utc=self.now.isoformat(), now=self.now)
        data.update(kwargs)
        return swing_evidence(**data)

    def test_detects_strict_local_pivots_but_never_attests(self):
        result = self.run_extractor()
        self.assertEqual(result["status"], "STRUCTURE_FOUND")
        self.assertIn((2, 17), result["swing_highs"])
        self.assertIn((5, 7), result["swing_lows"])
        self.assertFalse(result["verified"])
        self.assertFalse(result["trade_ready"])

    def test_missing_source_fails_closed(self):
        self.assertEqual(self.run_extractor(source="")["status"], "UNKNOWN")

    def test_stale_dataset_fails_closed(self):
        old = (self.now - timedelta(minutes=20)).isoformat()
        self.assertEqual(self.run_extractor(checked_utc=old)["status"], "UNKNOWN")

    def test_nan_and_inverted_ohlc_fail_closed(self):
        bad = list(self.bars)
        bad[1] = {"low": 15, "high": 12, "close": 13}
        self.assertEqual(self.run_extractor(bars=bad)["status"], "UNKNOWN")
        bad[1] = {"low": 9, "high": float("nan"), "close": 11}
        self.assertEqual(self.run_extractor(bars=bad)["status"], "UNKNOWN")

    def test_no_pivots_remains_incomplete(self):
        ascending = [{"low": i, "high": i + 2, "close": i + 1} for i in range(1, 10)]
        self.assertEqual(self.run_extractor(bars=ascending)["status"], "STRUCTURE_INCOMPLETE")

    def test_invalid_window_fails_closed(self):
        self.assertEqual(self.run_extractor(window=0)["status"], "UNKNOWN")
        self.assertEqual(self.run_extractor(window=True)["status"], "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
