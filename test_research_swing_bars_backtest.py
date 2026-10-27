"""Synthetic end-to-end backtest regression."""
import unittest
from datetime import date
from decimal import Decimal
from research_swing_bars_backtest import backtest_bars_and_signals


class BarsBacktestTests(unittest.TestCase):
    def test_next_open_cash_equity_and_drawdown(self):
        days = [date(2026, 1, n) for n in (2, 5, 6, 7)]
        bars = [{"date": day, "open": op, "close": close}
                for day, op, close in zip(days,
                                          [100, 100, 100, 110],
                                          [100, 100, 80, 110])]
        result = backtest_bars_and_signals(
            {"A": bars}, [{"ticker": "A", "decision_index": 0,
                           "score": 1}], days,
            horizon=2, initial_capital=3500, tranche=3500,
            roundtrip_cost_bps=50)
        self.assertEqual(Decimal(result["cash_accounting"]["ending_cash"]),
                         Decimal("3832.5"))
        self.assertEqual(Decimal(result["equity"]["max_drawdown_pct"]),
                         Decimal("-20"))
        self.assertFalse(result["historical_edge_proven"])

    def test_ineligible_dataset_manifest_rejected(self):
        days = [date(2026, 1, n) for n in (2, 5, 6)]
        bars = [{"date": d, "open": 100, "close": 100} for d in days]
        manifest = {
            "dataset_id": "synthetic", "market": "US",
            "source_url": "https://example.org/synthetic",
            "retrieved_at": "2026-10-26T12:00:00Z",
            "as_of_at": "2026-10-25T12:00:00Z",
            "price_adjustment": "split_adjusted", "currency": "USD",
            "includes_delisted": False, "license_reviewed": True,
            "event_timestamp_policy": "independently_verified",
        }
        with self.assertRaisesRegex(ValueError, "dataset_not_comparison_eligible"):
            backtest_bars_and_signals(
                {"A": bars}, [{"ticker": "A", "decision_index": 0,
                               "score": 1}], days, horizon=1,
                initial_capital=3500, dataset_manifest=manifest)

    def test_missing_close_fails_closed(self):
        days = [date(2026, 1, n) for n in (2, 5, 6)]
        bars = [{"date": d, "open": 100, "close": 0 if i == 1 else 100}
                for i, d in enumerate(days)]
        with self.assertRaisesRegex(ValueError, "invalid_close_price"):
            backtest_bars_and_signals(
                {"A": bars}, [{"ticker": "A", "decision_index": 0,
                               "score": 1}], days,
                horizon=1, initial_capital=3500)


if __name__ == "__main__":
    unittest.main()
