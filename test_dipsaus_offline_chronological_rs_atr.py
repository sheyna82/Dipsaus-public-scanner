import unittest
from datetime import date, timedelta
from dipsaus_offline_chronological_rs_atr import chronological_rs_atr_diagnostic


def bars(n=500, growth=0.3):
    rows = []
    for i in range(n):
        c = 100 + growth * i + (i % 17) * 0.02
        rows.append({"date": (date(2024, 1, 1) + timedelta(days=i)).isoformat(),
                     "open": c, "high": c + 1, "low": c - 1,
                     "close": c, "volume": 1000})
    return rows


class ChronologicalRSATRTests(unittest.TestCase):
    def test_train_only_thresholds_and_no_trade_claim(self):
        r = chronological_rs_atr_diagnostic(bars(), bars(growth=0.15),
                                             min_train=5, min_test=3)
        self.assertEqual(r["status"], "EXPLORATORY_CHRONOLOGICAL_DIAGNOSTIC")
        self.assertIn("missed_winning_events", r["factors"]["rs"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["independent_untouched_holdout"])

    def test_unsupported_short_split_is_blocked(self):
        r = chronological_rs_atr_diagnostic(bars(n=90), bars(n=90, growth=0.15))
        self.assertEqual(r["status"], "DATA_BLOCKED")

    def test_embargo_cannot_be_shorter_than_exit_horizon(self):
        r = chronological_rs_atr_diagnostic(bars(), bars(growth=0.15),
                                             embargo_sessions=3)
        self.assertEqual(r["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
