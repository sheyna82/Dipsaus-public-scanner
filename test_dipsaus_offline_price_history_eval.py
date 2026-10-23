import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path
from dipsaus_offline_price_history_eval import evaluate_local_history


def make_csv(count=90):
    start = date(2025, 1, 1)
    lines = ["Date,Open,High,Low,Close,Volume"]
    for i in range(count):
        price = 100 + i * 0.4
        lines.append(f"{(start + timedelta(days=i)).isoformat()},{price},{price+1},{price-1},{price},1000")
    return "\n".join(lines) + "\n"


class HistoryEvaluationTests(unittest.TestCase):
    def test_next_open_comparison_is_research_only(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.csv", Path(folder) / "b.csv"
            a.write_text(make_csv(), encoding="utf-8")
            b.write_text(make_csv(), encoding="utf-8")
            r = evaluate_local_history(a, b)
            self.assertEqual(r["status"], "EXPLORATORY_ONLY")
            self.assertGreater(r["observations"], 0)
            self.assertFalse(r["trade_ready"])
            self.assertFalse(r["earnings_calendar_verified"])
            self.assertEqual(r["rows"][0]["signal_date"], "2025-01-22")
            self.assertEqual(r["rows"][0]["exit_date"], "2025-02-02")

    def test_missing_or_invalid_input(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.csv", Path(folder) / "b.csv"
            a.write_text(make_csv(), encoding="utf-8")
            b.write_text(make_csv(89), encoding="utf-8")
            self.assertEqual(evaluate_local_history(a, b)["reason"], "unaligned_sessions")
            self.assertEqual(evaluate_local_history(a, b, horizon=0)["reason"], "invalid_horizon")
            self.assertEqual(evaluate_local_history(a, b, fee_bps=-1)["reason"], "invalid_fees")


if __name__ == "__main__":
    unittest.main()
