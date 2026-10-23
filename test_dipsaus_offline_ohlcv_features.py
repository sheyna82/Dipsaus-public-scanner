import unittest
from datetime import date, timedelta
from dipsaus_offline_ohlcv_features import calculate_recovery_features


def bars(multiplier=1, volume=100):
    start = date(2026, 9, 1)
    return [{"date": (start + timedelta(days=i)).isoformat(),
             "open": (100 + i) * multiplier,
             "high": (101 + i) * multiplier,
             "low": (99 + i) * multiplier,
             "close": (100 + i) * multiplier,
             "volume": volume} for i in range(23)]


class OhlcvFeaturesTests(unittest.TestCase):
    def test_causal_features_and_benchmark(self):
        stock = bars()
        benchmark = bars()
        stock[-1]["volume"] = 150
        r = calculate_recovery_features(stock, benchmark, 12)
        self.assertAlmostEqual(r["relative_strength_20d"], 0)
        self.assertAlmostEqual(r["volume_ratio_20d"], 1.5)
        self.assertEqual(r["days_to_earnings"], 12)
        self.assertGreater(r["atr_pct"], 0)

    def test_latest_bar_matters_only_when_supplied(self):
        stock = bars()
        base = calculate_recovery_features(stock[:-1], bars()[:-1], 10)
        stock[-1]["close"] = 121
        changed = calculate_recovery_features(stock, bars(), 10)
        self.assertNotEqual(base["return_5d"], changed["return_5d"])

    def test_rejects_misaligned_benchmark(self):
        benchmark = bars()
        benchmark[-1]["date"] = "2026-10-01"
        self.assertIsNone(calculate_recovery_features(bars(), benchmark, 10))

    def test_rejects_bad_ohlcv_and_unknown_earnings(self):
        stock = bars()
        stock[-1]["high"] = 1
        self.assertIsNone(calculate_recovery_features(stock, bars(), 10))
        self.assertIsNone(calculate_recovery_features(bars(), bars(), None))


if __name__ == "__main__":
    unittest.main()
