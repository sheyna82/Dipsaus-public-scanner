"""Offline source-comparison contract tests; all data synthetic."""
import hashlib
import unittest
from datetime import datetime, timezone
from research.us_ohlcv_integrity_20261117 import canonical_payload
from research.us_source_comparison_20261117 import compare_sources


class SourceComparisonTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 9, tzinfo=timezone.utc)
        bars = [{"time": f"2026-11-{d:02d}T16:00:00Z", "open": 100 + d,
                 "high": 102 + d, "low": 99 + d, "close": 101 + d,
                 "volume": 1000} for d in range(1, 9)]
        self.left = self.item("provider-A", bars)
        self.right = self.item("provider-B", bars)

    def item(self, source, bars):
        return {"source": source, "bars": bars, "instrument": "SYNTH",
                "timeframe": "daily", "adjustment": "raw",
                "fetched_utc": self.now.isoformat(),
                "expected_sha256": hashlib.sha256(canonical_payload(bars)).hexdigest()}

    def check(self, left=None, right=None):
        return compare_sources(self.left if left is None else left,
                               self.right if right is None else right, now=self.now)

    def test_matching_bars_still_not_independent_attestation(self):
        result = self.check()
        self.assertEqual(result["status"], "CROSS_SOURCE_CONSISTENT")
        self.assertFalse(result["provider_independently_verified"])
        self.assertFalse(result["trade_ready"])

    def test_same_provider_rejected(self):
        self.assertIn("SAME_PROVIDER", self.check(right=dict(self.right, source="provider-A"))["blocks"])

    def test_different_instrument_rejected(self):
        self.assertIn("INSTRUMENT_OR_TIMEFRAME_MISMATCH",
                      self.check(right=dict(self.right, instrument="OTHER"))["blocks"])

    def test_adjustment_policy_rejected(self):
        self.assertIn("ADJUSTMENT_POLICY_MISMATCH",
                      self.check(right=dict(self.right, adjustment="split"))["blocks"])

    def test_changed_price_detected_even_with_updated_digest(self):
        bars = [dict(b) for b in self.right["bars"]]
        bars[2]["close"] += 1
        right = self.item("provider-B", bars)
        self.assertIn("PRICE_DISAGREEMENT", self.check(right=right)["blocks"])

    def test_missing_digest_fails(self):
        right = dict(self.right)
        right.pop("expected_sha256")
        self.assertIn("RIGHT_METADATA_MISSING", self.check(right=right)["blocks"])


if __name__ == "__main__":
    unittest.main()
