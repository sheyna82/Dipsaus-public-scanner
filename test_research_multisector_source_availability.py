import json
from datetime import datetime, timezone, timedelta
import unittest
from research_multisector_source_availability import CANDIDATES, inspect_candidate


class SourceAvailabilityTests(unittest.TestCase):
    def test_current_day_malformed_bar_is_discarded(self):
        today = datetime.now(timezone.utc).date()
        dates = [today - timedelta(days=3), today - timedelta(days=2), today - timedelta(days=1), today]
        # Provide sufficient history for the strict 22-bar audit.
        dates = [today - timedelta(days=i) for i in range(30, 0, -1)] + [today]
        stamps = [int(datetime(d.year, d.month, d.day, 16, tzinfo=timezone.utc).timestamp())
                  for d in dates]
        q = {"open": [100.] * len(dates), "high": [101.] * len(dates),
             "low": [99.] * len(dates), "close": [100.] * len(dates),
             "volume": [1000] * len(dates)}
        q["high"][-1] = 90.
        payload = {"chart": {"result": [{"meta": {"symbol": "DIS"},
                                         "timestamp": stamps,
                                         "indicators": {"quote": [q]}}]}}
        result = inspect_candidate("DIS", "Communication Services", "active",
                                   fetch=lambda url: json.dumps(payload).encode())
        self.assertEqual(result["status"], "OHLCV_VALIDATED")
        self.assertEqual(result["discarded_unconfirmed_bars"], 1)

    def test_declared_universe_contains_delisted(self):
        self.assertEqual(len(CANDIDATES), 12)
        self.assertIn("delisted", {row[2] for row in CANDIDATES})
        self.assertEqual(len({row[1] for row in CANDIDATES}), 11)

    def test_rejects_invalid_source(self):
        result = inspect_candidate("XOM", "Energy", "active",
                                   fetch=lambda url: b'{"chart":{"result":null}}')
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertFalse(result["trade_ready"])

    def test_does_not_claim_price_verification(self):
        result = inspect_candidate("LEH", "Financials", "delisted",
                                   fetch=lambda url: b'{}')
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["delisted_coverage_verified"])


if __name__ == "__main__":
    unittest.main()
