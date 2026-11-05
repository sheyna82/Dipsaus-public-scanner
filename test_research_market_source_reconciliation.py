"""Synthetic offline source reconciliation tests."""
import unittest
from research_market_source_reconciliation import reconcile_daily_sources


class SourceReconciliationTests(unittest.TestCase):
    def test_detects_vendor_disagreement(self):
        data = {
            "vendor_a": [{"date": "2026-10-21", "close": "100"},
                         {"date": "2026-10-22", "close": "102"}],
            "vendor_b": [{"date": "2026-10-21", "close": "100.1"},
                         {"date": "2026-10-22", "close": "106"}],
        }
        result = reconcile_daily_sources(data, adjustment_mode="raw")
        self.assertEqual(result["common_sessions"], 2)
        self.assertTrue(result["compared_sessions"][0]["within_tolerance"])
        self.assertFalse(result["compared_sessions"][1]["within_tolerance"])
        self.assertFalse(result["all_within_tolerance"])
        self.assertFalse(result["trade_ready"])

    def test_requires_two_sources_and_explicit_adjustment(self):
        rows = [{"date": "2026-10-21", "close": 100}]
        with self.assertRaisesRegex(ValueError, "two_independent_sources_required"):
            reconcile_daily_sources({"one": rows}, adjustment_mode="raw")
        with self.assertRaisesRegex(ValueError, "adjustment_mode_required"):
            reconcile_daily_sources({"a": rows, "b": rows}, adjustment_mode="unknown")

    def test_rejects_invalid_and_nonoverlapping(self):
        with self.assertRaisesRegex(ValueError, "no_overlapping_sessions"):
            reconcile_daily_sources({
                "a": [{"date": "2026-10-21", "close": 100}],
                "b": [{"date": "2026-10-22", "close": 100}]}, adjustment_mode="raw")
        with self.assertRaisesRegex(ValueError, "invalid_session_price"):
            reconcile_daily_sources({
                "a": [{"date": "2026-10-21", "close": "NaN"}],
                "b": [{"date": "2026-10-21", "close": 100}]}, adjustment_mode="raw")


if __name__ == "__main__":
    unittest.main()
