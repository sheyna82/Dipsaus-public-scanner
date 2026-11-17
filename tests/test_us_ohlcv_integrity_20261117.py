"""Isolated offline tests: digest consistency does not attest market truth."""
import hashlib
import unittest
from datetime import datetime, timezone, timedelta
from research.us_ohlcv_integrity_20261117 import attest_ohlcv, canonical_payload


class OHLCVIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 9, tzinfo=timezone.utc)
        self.bars = [
            {"time": f"2026-11-{d:02d}T16:00:00Z",
             "open": 10.0 + d, "high": 11.0 + d, "low": 9.0 + d,
             "close": 10.5 + d, "volume": 1000}
            for d in range(1, 9)
        ]
        self.digest = hashlib.sha256(canonical_payload(self.bars)).hexdigest()

    def check(self, bars=None, digest=None, **kw):
        args = dict(source="fixture-provider", instrument="SYNTH",
                    timeframe="daily", fetched_utc=self.now.isoformat(),
                    expected_sha256=self.digest, now=self.now)
        args.update(kw)
        return attest_ohlcv(self.bars if bars is None else bars,
                            expected_sha256=digest if digest is not None else args.pop("expected_sha256"),
                            **args)

    def test_canonical_match_never_verifies_provider(self):
        r = self.check()
        self.assertEqual(r["status"], "INTEGRITY_MATCH")
        self.assertFalse(r["provider_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_changed_close_breaks_digest(self):
        bars = [dict(b) for b in self.bars]
        bars[3]["close"] += .1
        self.assertIn("SHA256_MISMATCH", self.check(bars=bars)["blocks"])

    def test_missing_source_fails(self):
        self.assertEqual(self.check(source="")["status"], "UNKNOWN")

    def test_duplicate_timestamps_fail(self):
        bars = [dict(b) for b in self.bars]
        bars[4]["time"] = bars[3]["time"]
        self.assertIn("BAR_TIME_NOT_STRICTLY_INCREASING", self.check(bars=bars)["blocks"])

    def test_nonfinite_price_fails(self):
        bars = [dict(b) for b in self.bars]
        bars[2]["close"] = float("nan")
        self.assertIn("BAR_NUMERIC_INVALID", self.check(bars=bars)["blocks"])

    def test_stale_fetch_fails(self):
        stamp = (self.now - timedelta(hours=1)).isoformat()
        self.assertEqual(self.check(fetched_utc=stamp)["status"], "UNKNOWN")

    def test_inverted_candle_fails(self):
        bars = [dict(b) for b in self.bars]
        bars[2]["low"] = bars[2]["high"] + 1
        self.assertIn("BAR_OHLC_RANGE_INVALID", self.check(bars=bars)["blocks"])


if __name__ == "__main__":
    unittest.main()
