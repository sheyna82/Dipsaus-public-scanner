"""Offline Massive adapter regression tests with synthetic candles only."""
import unittest
from research.us_massive_adapter_20261117 import normalize_massive_aggregates

class MassiveAdapterTests(unittest.TestCase):
    def setUp(self):
        self.payload = {"ticker": "SYNTH", "adjusted": False, "results": [
            {"t": 1700000000000 + i * 86400000, "o": 10, "h": 12, "l": 9, "c": 11, "v": 100}
            for i in range(8)]}
    def check(self, payload=None, **kwargs):
        args = {"ticker": "SYNTH", "mic": "XNAS", "adjustment_policy": "unadjusted"}
        args.update(kwargs)
        return normalize_massive_aggregates(self.payload if payload is None else payload, **args)
    def test_valid_remains_unverified(self):
        r = self.check()
        self.assertEqual(r["status"], "NORMALIZED_UNVERIFIED")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["provider_independently_verified"])
        self.assertEqual(len(r["bars"]), 8)
    def test_missing_adjustment_metadata(self):
        p = dict(self.payload)
        p.pop("adjusted")
        self.assertIn("ADJUSTMENT_METADATA_MISSING", self.check(p)["blocks"])
    def test_conflicting_adjustment_metadata(self):
        self.assertIn("ADJUSTMENT_MISMATCH", self.check({**self.payload, "adjusted": True})["blocks"])
    def test_missing_results(self):
        self.assertIn("RESULTS_MISSING", self.check({"ticker": "SYNTH"})["blocks"])
    def test_wrong_ticker(self):
        self.assertIn("TICKER_MISMATCH", self.check(ticker="OTHER")["blocks"])
    def test_unknown_adjustment(self):
        self.assertIn("ADJUSTMENT_POLICY_UNKNOWN", self.check(adjustment_policy="unknown")["blocks"])
    def test_duplicate_timestamp(self):
        p = {"ticker": "SYNTH", "adjusted": False, "results": [dict(b) for b in self.payload["results"]]}
        p["results"][2]["t"] = p["results"][1]["t"]
        self.assertIn("TIMESTAMP_INVALID_OR_UNSORTED", self.check(p)["blocks"])
    def test_nan_rejected(self):
        p = {"ticker": "SYNTH", "adjusted": False, "results": [dict(b) for b in self.payload["results"]]}
        p["results"][0]["c"] = float("nan")
        self.assertIn("BAR_NUMERIC_INVALID", self.check(p)["blocks"])
    def test_negative_volume(self):
        p = {"ticker": "SYNTH", "adjusted": False, "results": [dict(b) for b in self.payload["results"]]}
        p["results"][0]["v"] = -1
        self.assertIn("BAR_OHLC_INVALID", self.check(p)["blocks"])

if __name__ == "__main__":
    unittest.main()
