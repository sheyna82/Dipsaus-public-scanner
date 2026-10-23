import unittest
from datetime import date, timedelta
from dipsaus_offline_structure_regime_diagnostic import evaluate_structure_regime


def bars(n=500, growth=0.3):
    rows = []
    for i in range(n):
        close = 100 + growth*i + (i % 17)*0.02
        rows.append({"date": (date(2024, 1, 1)+timedelta(days=i)).isoformat(),
                     "open": close, "high": close+1, "low": close-1,
                     "close": close, "volume": 1000})
    return rows


class StructureRegimeTests(unittest.TestCase):
    def test_chronological_and_no_trade_claim(self):
        r = evaluate_structure_regime(bars(), bars(growth=0.15), min_train=5, min_test=3)
        self.assertEqual(r["status"], "EXPLORATORY_STRUCTURE_REGIME_DIAGNOSTIC")
        self.assertEqual(set(r["factors"]), {"structure_above_20d_mean", "atr_expanding", "market_20d_positive"})
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["independent_untouched_holdout"])

    def test_short_history_blocks(self):
        r = evaluate_structure_regime(bars(90), bars(90, growth=0.15))
        self.assertEqual(r["status"], "DATA_BLOCKED")

    def test_invalid_embargo_blocks(self):
        r = evaluate_structure_regime(bars(), bars(growth=0.15), embargo_sessions=3)
        self.assertEqual(r["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
