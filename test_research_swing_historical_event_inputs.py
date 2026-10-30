"""Offline tests for historical event provenance and price quality."""
import unittest
from research_swing_historical_event_inputs import (
    validate_historical_event_rows, validate_daily_bars)

def event():
    return {"symbol": "ABC", "event_id": "release-1", "kind": "earnings_release",
            "source": "issuer", "source_url": "https://example.org/release",
            "published_at": "2026-10-26T16:01:00-04:00",
            "first_observed_at": "2026-10-26T16:02:00-04:00",
            "release_timestamp_verified": True}

def bar(day, **changes):
    result = {"open_at": f"2026-10-{day:02d}T09:30:00-04:00",
              "close_at": f"2026-10-{day:02d}T16:00:00-04:00",
              "open": 100, "high": 105, "low": 98, "close": 102}
    result.update(changes)
    return result

class HistoricalInputTests(unittest.TestCase):
    def test_sourced_event_accepted(self):
        records = validate_historical_event_rows([event()], cutoff_at="2026-10-27T00:00:00Z")
        self.assertEqual(len(records), 1)
        self.assertFalse(records[0]["trade_ready"])
    def test_future_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "event_after_cutoff"):
            validate_historical_event_rows([event()], cutoff_at="2026-10-26T18:00:00Z")
    def test_missing_source_url_rejected(self):
        row = event()
        row.pop("source_url")
        with self.assertRaisesRegex(ValueError, "missing_source_url"):
            validate_historical_event_rows([row], cutoff_at="2026-10-27T00:00:00Z")
    def test_duplicate_event_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_event"):
            validate_historical_event_rows([event(), event()], cutoff_at="2026-10-27T00:00:00Z")
    def test_unverified_release_rejected(self):
        row = event()
        row["release_timestamp_verified"] = False
        with self.assertRaisesRegex(ValueError, "unverified_release_time"):
            validate_historical_event_rows([row], cutoff_at="2026-10-27T00:00:00Z")
    def test_valid_bars(self):
        self.assertEqual(validate_daily_bars([bar(26), bar(27)]), 2)
    def test_bad_ohlc_rejected(self):
        with self.assertRaisesRegex(ValueError, "inconsistent_ohlc"):
            validate_daily_bars([bar(26, low=103)])
    def test_out_of_order_bars_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_bar_order"):
            validate_daily_bars([bar(27), bar(26)])
    def test_nonfinite_price_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_ohlc"):
            validate_daily_bars([bar(26, high=float("nan"))])

if __name__ == "__main__":
    unittest.main()
