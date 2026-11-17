"""Offline composition gate regression checks."""
import hashlib
import unittest
from datetime import datetime, timezone, timedelta
from research.us_massive_adapter_20261117 import normalize_massive_aggregates
from research.us_ohlcv_integrity_20261117 import canonical_payload
from research.us_massive_pipeline_20261117 import assess_massive_fixture

class MassivePipelineTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 12, tzinfo=timezone.utc)
        # Synthetic weekday dates at 10:30 NY local, Nov 2-10 2026.
        self.payload = {"ticker": "SYNTH", "adjusted": False, "results": [
            {"t": int(datetime(2026, 11, d, 15, 30, tzinfo=timezone.utc).timestamp()*1000),
             "o": 10, "h": 12, "l": 9, "c": 11, "v": 100}
            for d in (2, 3, 4, 5, 6, 9, 10)]}
        bars = normalize_massive_aggregates(self.payload, ticker="SYNTH",
                mic="XNAS", adjustment_policy="unadjusted")["bars"]
        self.digest = hashlib.sha256(canonical_payload(bars)).hexdigest()
    def check(self, payload=None, **changes):
        args = dict(ticker="SYNTH", mic="XNAS", adjustment_policy="unadjusted",
                    timeframe="hourly", fetched_utc=self.now.isoformat(),
                    now=self.now, expected_sha256=self.digest)
        args.update(changes)
        return assess_massive_fixture(self.payload if payload is None else payload, **args)
    def test_valid_fixture_never_trade_ready(self):
        r = self.check()
        self.assertEqual(r["status"], "RESEARCH_SCREENED_UNVERIFIED")
        self.assertEqual(r["bar_count"], 7)
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["provider_independently_verified"])
        self.assertFalse(r["exchange_calendar_verified"])
    def test_digest_mismatch_blocks(self):
        self.assertIn("INTEGRITY_SHA256_MISMATCH", self.check(expected_sha256="0"*64)["blocks"])
    def test_stale_fetch_blocks(self):
        r = self.check(fetched_utc=(self.now-timedelta(days=1)).isoformat())
        self.assertIn("INTEGRITY_FETCH_TIME_INVALID_OR_STALE", r["blocks"])
    def test_bad_ticker_blocks(self):
        self.assertIn("NORMALIZATION_TICKER_MISMATCH", self.check(ticker="OTHER")["blocks"])
    def test_outside_session_blocks(self):
        p = {"ticker": "SYNTH", "adjusted": False, "results": [dict(x) for x in self.payload["results"]]}
        p["results"][0]["t"] -= 7200000
        bars = normalize_massive_aggregates(p, ticker="SYNTH", mic="XNAS",
                                             adjustment_policy="unadjusted")["bars"]
        digest = hashlib.sha256(canonical_payload(bars)).hexdigest()
        self.assertIn("SESSION_OUTSIDE_REGULAR_SESSION", self.check(p, expected_sha256=digest)["blocks"])
    def test_weekend_blocks(self):
        p = {"ticker": "SYNTH", "adjusted": False, "results": [dict(x) for x in self.payload["results"]]}
        p["results"][4]["t"] += 86400000
        bars = normalize_massive_aggregates(p, ticker="SYNTH", mic="XNAS",
                                             adjustment_policy="unadjusted")["bars"]
        digest = hashlib.sha256(canonical_payload(bars)).hexdigest()
        self.assertIn("SESSION_WEEKEND_BAR", self.check(p, expected_sha256=digest)["blocks"])

if __name__ == "__main__":
    unittest.main()
