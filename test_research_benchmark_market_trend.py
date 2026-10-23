"""Synthetic benchmark alignment tests."""
import unittest
from research_benchmark_market_trend import attach_market_trend, eligible_model_rows


def benchmark(n=25):
    lines = ["date,open,high,low,close,volume"]
    for i in range(1, n + 1):
        c = 100 + i
        lines.append(f"2026-01-{i:02d},{c},{c+1},{c-1},{c},100")
    return ("\n".join(lines) + "\n").encode()


class BenchmarkTests(unittest.TestCase):
    def test_causal_market_trend_and_missing_date(self):
        events = [{"date": "2026-01-20"}, {"date": "2026-01-21"},
                  {"date": "2026-01-25"}, {"date": "2026-01-26"}]
        result = attach_market_trend(events, benchmark())
        self.assertEqual([r["market_20d_positive"] for r in result],
                         [None, True, True, None])
        self.assertEqual(len(eligible_model_rows(result)), 2)
        self.assertTrue(all(not r["trade_ready"] for r in result))

    def test_future_append_does_not_rewrite_past(self):
        events = [{"date": "2026-01-21"}]
        self.assertEqual(attach_market_trend(events, benchmark(24)),
                         attach_market_trend(events, benchmark(25)))

    def test_invalid_lookback(self):
        with self.assertRaises(ValueError):
            attach_market_trend([], benchmark(), lookback=True)


if __name__ == "__main__":
    unittest.main()
