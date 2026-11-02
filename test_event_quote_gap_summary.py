"""Offline regression for privacy-preserving quote gap summaries."""
import unittest
from datetime import datetime, timezone
from event_quote_gap_summary import summarize_event_quote_gaps

class QuoteGapSummaryTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 2, 15, tzinfo=timezone.utc)

    def test_existing_watch_shape_blocks_and_counts_missing(self):
        rows = [{"symbol": "PLTR", "provider_quote": 100,
                 "provider_quote_utc": "2026-11-02T14:59:00+00:00",
                 "provider_freshness_pass": True}]
        result = summarize_event_quote_gaps(rows, self.now)
        self.assertEqual(result["blocked"], 1)
        self.assertEqual(result["validated_research_only"], 0)
        self.assertEqual(result["missing_counts"]["provider_source"], 1)
        self.assertEqual(result["missing_counts"]["market_session_verified"], 1)
        self.assertNotIn("PLTR", str(result))
        self.assertNotIn("100", str(result))
        self.assertFalse(result["execution_ready"])

    def test_non_list_input_is_blocked(self):
        self.assertEqual(summarize_event_quote_gaps({}, self.now)["status"], "INVALID_INPUT")

    def test_mixed_rows_never_enable_execution(self):
        rows = [{"symbol": "PLTR", "provider_symbol": "PLTR", "provider_currency": "USD",
                 "provider_quote": 100, "provider_quote_utc": "2026-11-02T14:59:00+00:00",
                 "provider_freshness_pass": True, "provider_source": "Yahoo Finance 1m",
                 "market_session_verified": True, "provider_delayed": False},
                {"symbol": "AMD"}]
        result = summarize_event_quote_gaps(rows, self.now)
        self.assertEqual((result["validated_research_only"], result["blocked"]), (1, 1))
        self.assertFalse(result["execution_ready"])

if __name__ == "__main__":
    unittest.main()
