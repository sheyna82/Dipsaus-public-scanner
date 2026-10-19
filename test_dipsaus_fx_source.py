import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
from dipsaus_fx_source import validated_eur_per_usd, fetch_fx

class FakeIndex(list):
    pass

class FakeSeries:
    def __init__(self, value): self.iloc = [value]

class FakeHistory:
    empty = False
    def __init__(self, stamp, close):
        self.index = [stamp]
        self.data = {"Close": FakeSeries(close)}
    def __getitem__(self, key): return self.data[key]

class FxTests(unittest.TestCase):
    def setUp(self): self.now = datetime(2026, 10, 19, 20, 0, tzinfo=timezone.utc)
    def test_fresh_conversion(self):
        result = validated_eur_per_usd(FakeHistory(self.now, 1.1), self.now)
        self.assertEqual(result["status"], "FX_FRESH")
        self.assertAlmostEqual(result["eur_per_usd"], 1/1.1)
        self.assertFalse(result["fx_broker_executable"])
    def test_stale(self):
        result = validated_eur_per_usd(FakeHistory(self.now-timedelta(minutes=3), 1.1), self.now)
        self.assertEqual(result["status"], "FX_STALE_OR_INVALID")
    def test_future_bar(self):
        result = validated_eur_per_usd(FakeHistory(self.now+timedelta(minutes=2), 1.1), self.now)
        self.assertEqual(result["status"], "FX_STALE_OR_INVALID")
    def test_zero(self):
        self.assertEqual(validated_eur_per_usd(FakeHistory(self.now, 0), self.now)["status"], "FX_STALE_OR_INVALID")
    def test_naive_timestamp(self):
        self.assertEqual(validated_eur_per_usd(FakeHistory(self.now.replace(tzinfo=None), 1.1), self.now)["status"], "FX_TIMEZONE_UNKNOWN")
    def test_missing(self):
        self.assertEqual(validated_eur_per_usd(None, self.now)["status"], "FX_UNAVAILABLE")
    def test_fetch_failure(self):
        yf = Mock(); yf.Ticker.side_effect = RuntimeError("provider error")
        self.assertEqual(fetch_fx(yf, self.now)["status"], "FX_UNAVAILABLE")

if __name__ == "__main__": unittest.main()
