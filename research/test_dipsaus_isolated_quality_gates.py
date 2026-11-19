"""Isolated research QA tests; no live scanner imports."""
import unittest
from datetime import datetime, timezone
from decimal import Decimal
from dipsaus_isolated_quality_gates import net_round_trip, verify_signal_freshness, pivot_confirmation_dates

class CostTests(unittest.TestCase):
    def test_spread_once(self):
        result = net_round_trip(shares=10, buy_ask=101, sell_bid=99,
            buy_eur_per_quote=1, sell_eur_per_quote=1, buy_broker_fee_eur=0,
            sell_broker_fee_eur=0, buy_fx_fee_eur=0, sell_fx_fee_eur=0)
        self.assertEqual(Decimal(result["net_realized_pnl_eur"]), Decimal(-20))
        self.assertFalse(result["broker_statement_reconciled"])

    def test_fx_direction_fees_slippage(self):
        result = net_round_trip(shares=10, buy_ask=100, sell_bid=110,
            buy_eur_per_quote="0.90", sell_eur_per_quote="0.80",
            buy_broker_fee_eur=2, sell_broker_fee_eur=3,
            buy_fx_fee_eur=1, sell_fx_fee_eur=1,
            buy_slippage_per_share=1, sell_slippage_per_share=2)
        self.assertEqual(Decimal(result["entry_cash_out_eur"]), Decimal(912))
        self.assertEqual(Decimal(result["exit_cash_in_eur"]), Decimal(860))
        self.assertEqual(Decimal(result["net_realized_pnl_eur"]), Decimal(-52))

    def test_invalid_values_and_basis(self):
        args = dict(shares=1, buy_ask=10, sell_bid=11, buy_eur_per_quote=1,
            sell_eur_per_quote=1, buy_broker_fee_eur=0, sell_broker_fee_eur=0,
            buy_fx_fee_eur=0, sell_fx_fee_eur=0)
        for bad in ("NaN", "Infinity", -1, True):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                net_round_trip(**dict(args, buy_broker_fee_eur=bad))
        with self.assertRaises(ValueError):
            net_round_trip(**dict(args, fx_basis="quote_per_eur"))
        with self.assertRaises(ValueError):
            net_round_trip(**dict(args, shares="0.5"))

class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 6, 17, tzinfo=timezone.utc)
        self.row = dict(provider_freshness_pass=True, prealert_trigger_observed=True,
            provider_quote_utc="2026-11-06T16:59:00Z",
            signal_generated_utc="2026-11-06T16:59:30Z")

    def test_fresh_is_not_authenticated(self):
        result = verify_signal_freshness(self.row, now=self.now)
        self.assertTrue(result["eligible"])
        self.assertFalse(result["source_authenticity_independently_proven"])

    def test_stale_overrides_upstream_flag(self):
        result = verify_signal_freshness(dict(self.row, provider_quote_utc="2026-11-06T16:50:00Z"), now=self.now)
        self.assertEqual(result["reason"], "STALE_INPUT")

    def test_missing_naive_future_rejected(self):
        for stamp in (None, "2026-11-06T16:59:00", "2026-11-06T17:02:00Z"):
            with self.subTest(stamp=stamp):
                self.assertFalse(verify_signal_freshness(dict(self.row, provider_quote_utc=stamp), now=self.now)["eligible"])

    def test_signal_before_quote_rejected(self):
        result = verify_signal_freshness(dict(self.row, signal_generated_utc="2026-11-06T16:58:00Z"), now=self.now)
        self.assertEqual(result["reason"], "SIGNAL_PRECEDES_QUOTE")

    def test_missing_upstream_confirmation_rejected(self):
        self.assertFalse(verify_signal_freshness(dict(self.row, provider_freshness_pass=False), now=self.now)["eligible"])

class PivotTests(unittest.TestCase):
    def test_pivot_requires_later_bars(self):
        highs = [10, 12, 15, 11, 9]
        rows = [dict(date=f"2026-11-{i+1:02}", open=8, close=8, high=h, low=7, volume=100)
                for i, h in enumerate(highs)]
        result = pivot_confirmation_dates(rows)
        self.assertEqual(result[0]["pivot_date"], "2026-11-03")
        self.assertEqual(result[0]["first_available_date"], "2026-11-05")

    def test_duplicate_dates_rejected(self):
        rows = [dict(date="2026-11-02", open=8, close=8, high=10, low=7, volume=100)]*5
        with self.assertRaisesRegex(ValueError, "UNSORTED_OR_DUPLICATE_DATES"):
            pivot_confirmation_dates(rows)

if __name__ == "__main__":
    unittest.main()
