import unittest
from datetime import date, timedelta
from dipsaus_offline_lookahead_audit import audit_future_invariance, frozen_signal_at


def history(n=45):
    result = []
    for i in range(n):
        close = 100 + i * 0.25
        result.append({"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                       "open": close, "high": close + 1, "low": close - 1,
                       "close": close, "volume": 1000})
    return result


class LookaheadAuditTests(unittest.TestCase):
    def test_future_bar_perturbation_does_not_change_prior_signal(self):
        r = audit_future_invariance(history(), indices=[21, 25, 35])
        self.assertEqual(r["status"], "EXPLORATORY_CAUSAL_INVARIANCE")
        self.assertEqual(r["checked_signals"], 3)
        self.assertFalse(r["trade_ready"])

    def test_original_and_future_modified_signals_identical(self):
        bars = history()
        before = frozen_signal_at(bars[:27], 26)
        bars[-1]["close"] *= 2
        bars[-1]["high"] *= 2
        self.assertEqual(before, frozen_signal_at(bars, 26))

    def test_rejects_future_or_early_index(self):
        self.assertEqual(audit_future_invariance(history(), indices=[44])["status"], "DATA_BLOCKED")
        self.assertEqual(frozen_signal_at(history(), 20)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
