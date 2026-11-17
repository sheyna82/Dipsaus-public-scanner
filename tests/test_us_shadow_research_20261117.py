"""Offline fail-closed regression tests for US shadow research."""
import unittest
from datetime import datetime, timezone, timedelta
from research.us_candidate_assessment_20261117 import assess_candidate
from research.us_level_evidence_20261117 import assess_levels
from research.us_trend_context_20261117 import assess_trend
from research.us_net_trade_20261117 import estimate_net_trade

class USResearchTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 17, 8, tzinfo=timezone.utc)
        stamp = self.now.isoformat()
        self.levels = {
            "quote": {"value": 100, "source": "independent_quote", "checked_utc": stamp, "verified": True},
            "resistance": {"value": 112, "source": "independent_resistance", "checked_utc": stamp, "verified": True, "dataset_id": "ohlcv-A", "method": "confirmed_swing_high", "timeframe": "daily"},
            "invalidation": {"value": 96, "source": "independent_structure", "checked_utc": stamp, "verified": True, "dataset_id": "ohlcv-B", "method": "confirmed_swing_low", "timeframe": "hourly"},
        }
        self.broker = {"ask": 100.1, "bid": 100, "source": "verified_broker", "checked_utc": stamp, "verified": True}
        self.fx = {"eur_per_usd": 0.9, "source": "verified_execution_fx", "checked_utc": stamp, "verified": True}
        self.costs = {"buy_fee_eur": 5, "sell_fee_eur": 5, "fx_cost_eur": 10, "slippage_eur": 10, "verified": True, "source": "broker_fee_schedule", "checked_utc": stamp}
        self.timeframes = {k: {"checked_utc": stamp, "source": k, "verified": True, "higher_low": True, "reclaim": True}
                           for k in ("intraday", "hourly", "daily")}

    def test_valid_research_never_trade_ready(self):
        data = dict(self.levels, symbol="SYNTH", broker=self.broker, fx=self.fx, costs=self.costs,
                    timeframes=self.timeframes, news_verified=True, events_verified=True,
                    portfolio_fit_verified=True, instrument_verified=True, broker_route_verified=True)
        result = assess_candidate(data, self.now)
        self.assertEqual(result["status"], "RESEARCH_CANDIDATE")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["notify"])
        self.assertFalse(result["automatic_orders"])

    def test_missing_resistance_fails_closed(self):
        r = assess_levels(self.levels["quote"], None, self.levels["invalidation"], self.now)
        self.assertEqual(r["status"], "UNKNOWN")

    def test_pivot_cannot_be_independent_resistance(self):
        resistance = dict(self.levels["resistance"], source="route_2_break_above")
        r = assess_levels(self.levels["quote"], resistance, self.levels["invalidation"], self.now)
        self.assertIn(r["status"], ("BLOCK", "UNKNOWN"))

    def test_intraday_only_cannot_confirm_swing(self):
        self.assertEqual(assess_trend({"intraday": self.timeframes["intraday"]}, self.now)["status"], "INCOMPLETE")

    def test_broker_missing_blocks_money(self):
        levels = assess_levels(**self.levels, now=self.now)
        self.assertEqual(estimate_net_trade(None, levels, self.fx, self.costs, now=self.now)["status"], "UNKNOWN")

    def test_unverified_fx_blocks_money(self):
        levels = assess_levels(**self.levels, now=self.now)
        self.assertEqual(estimate_net_trade(self.broker, levels, dict(self.fx, verified=False), self.costs, now=self.now)["status"], "UNKNOWN")

    def test_stale_broker_blocks_money(self):
        levels = assess_levels(**self.levels, now=self.now)
        broker = dict(self.broker, checked_utc=(self.now-timedelta(minutes=3)).isoformat())
        self.assertEqual(estimate_net_trade(broker, levels, self.fx, self.costs, now=self.now)["status"], "UNKNOWN")

    def test_missing_cost_provenance_fails_closed(self):
        levels = assess_levels(**self.levels, now=self.now)
        costs = dict(self.costs)
        costs.pop("source")
        self.assertEqual(estimate_net_trade(self.broker, levels, self.fx, costs, now=self.now)["status"], "UNKNOWN")

    def test_missing_structural_dataset_fails_closed(self):
        resistance = dict(self.levels["resistance"])
        resistance.pop("dataset_id")
        self.assertEqual(assess_levels(self.levels["quote"], resistance, self.levels["invalidation"], self.now)["status"], "UNKNOWN")

    def test_missing_news_prevents_candidate(self):
        data = dict(self.levels, symbol="SYNTH", broker=self.broker, fx=self.fx, costs=self.costs, timeframes=self.timeframes)
        self.assertEqual(assess_candidate(data, self.now)["status"], "INCOMPLETE_OR_BLOCKED")

if __name__ == "__main__":
    unittest.main()
