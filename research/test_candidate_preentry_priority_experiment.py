"""Fail-closed tests for pre-entry candidate priority experiments."""
import unittest
from candidate_preentry_priority_experiment import priority_experiment, entry_quarter_attribution, selection_difference_attribution, volume_leave_one_symbol_out


def row(symbol, ret, strength, day=10, selected=True):
    return {
        "symbol": symbol, "entry_day": day, "exit_day": day + 5,
        "filter_selected": selected,
        "historical_net_return_pct_outcome_not_selection_input": ret,
        "features_at_signal_close": {
            "relative_strength_20d_pct": strength,
            "atr_14_pct": 2.0,
            "volume_ratio_20d": 1.0
        }
    }


class PreentryPriorityTests(unittest.TestCase):
    def test_combined_priority_reuses_quarter_and_pnl_bridge(self):
        rows = [row(f"S{i:02d}", 10.0 if i == 6 else 0.0, i / 10.0)
                for i in range(7)]
        for event in rows:
            event["features_at_signal_close"]["status"] = "DESCRIPTIVE_ONLY"
            event["training_thresholds"] = {
                "relative_strength_20d_pct": 0.0,
                "volume_ratio_20d": 1.0, "atr_14_pct": 3.0}
        result = priority_experiment({
            "candidate_audit": rows,
            "baseline": {"accepted_n": 6, "realized_pnl": 0.0},
            "filtered": {"accepted_n": 6, "realized_pnl": 0.0}
        })
        combined = result["cohorts"]["baseline"]["scenarios"]["combined_predeclared"]
        self.assertEqual(combined["accepted_n"], 6)
        self.assertEqual(combined["realized_pnl"], 350.0)
        self.assertEqual(combined["selection_difference_attribution"]["pnl_bridge_difference"], 350.0)
        self.assertTrue(combined["entry_quarter_attribution"])
        self.assertFalse(combined["trade_ready"])

    def test_combined_leave_one_symbol_out_replays_capacity(self):
        rows = [row(f"S{i:02d}", 10.0 if i == 6 else 0.0, i / 10.0)
                for i in range(7)]
        for event in rows:
            event["features_at_signal_close"]["status"] = "DESCRIPTIVE_ONLY"
            event["training_thresholds"] = {
                "relative_strength_20d_pct": 0.0,
                "volume_ratio_20d": 1.0, "atr_14_pct": 3.0}
        result = priority_experiment({
            "candidate_audit": rows,
            "baseline": {"accepted_n": 6, "realized_pnl": 0.0},
            "filtered": {"accepted_n": 6, "realized_pnl": 0.0}
        })
        omitted = result["cohorts"]["baseline"]["scenarios"]["combined_predeclared"]["combined_leave_one_symbol_out"]
        self.assertEqual(omitted["symbol_count"], 7)
        self.assertEqual(omitted["omissions"]["S06"]["difference_eur"], 0.0)
        self.assertEqual(omitted["omissions"]["S00"]["difference_eur"], 0.0)
        self.assertEqual(omitted["omissions"]["S00"]["combined_accepted_n"], 6)
        self.assertFalse(omitted["trade_ready"])

    def test_score_uses_features_not_future_outcome(self):
        rows = [row(f"S{i:02d}", 10.0 if i == 6 else 0.0, float(i)) for i in range(7)]
        result = priority_experiment({
            "candidate_audit": rows,
            "baseline": {"accepted_n": 6, "realized_pnl": 0.0},
            "filtered": {"accepted_n": 6, "realized_pnl": 0.0}
        })
        scenarios = result["cohorts"]["baseline"]["scenarios"]
        self.assertEqual(scenarios["relative_strength_desc"]["accepted_n"], 6)
        self.assertEqual(scenarios["relative_strength_desc"]["realized_pnl"], 350.0)
        self.assertEqual(scenarios["relative_strength_asc"]["realized_pnl"], 0.0)
        overlap = scenarios["relative_strength_desc"]["accepted_trade_overlap_vs_neutral"]
        self.assertEqual(overlap["shared_n"], 5)
        self.assertEqual(overlap["only_neutral_n"], 1)
        self.assertEqual(overlap["only_priority_n"], 1)
        self.assertFalse(result["trade_ready"])

    def test_volume_leave_one_symbol_out_replays_capacity(self):
        events = [
            {"symbol": f"S{i:02d}", "entry_day": 10, "exit_day": 15,
             "net_return_pct": float(i), "features": {"volume_ratio_20d": float(i)}}
            for i in range(7)
        ]
        report = volume_leave_one_symbol_out(events)
        self.assertEqual(report["symbol_count"], 7)
        self.assertEqual(len(report["omissions"]), 7)
        self.assertEqual(report["positive_count"] + report["nonpositive_count"], 7)
        self.assertEqual(report["omissions"]["S06"]["difference_eur"], 0)
        self.assertFalse(report["trade_ready"])

    def test_entry_quarter_attribution_is_not_portfolio_return(self):
        from datetime import datetime, timezone
        day = lambda y, m: int(datetime(y, m, 15, tzinfo=timezone.utc).timestamp() // 86400)
        sim = {'accepted_signals': [
            {'entry_day': day(2025, 1), 'net_return_pct': 10},
            {'entry_day': day(2025, 3), 'net_return_pct': -2},
            {'entry_day': day(2025, 4), 'net_return_pct': 5}]}
        quarters = entry_quarter_attribution(sim)
        self.assertEqual(quarters['2025Q1']['trades_n'], 2)
        self.assertEqual(quarters['2025Q1']['entry_attributed_pnl'], 280.0)
        self.assertEqual(quarters['2025Q2']['entry_attributed_pnl'], 175.0)

    def test_pnl_bridge_and_extra_cost_stress(self):
        neutral = {"accepted_signals": [
            {"symbol": "AAA", "entry_day": 1, "net_return_pct": 2.0}],
            "accepted_n": 1, "realized_pnl": 70.0}
        priority = {"accepted_signals": [
            {"symbol": "BBB", "entry_day": 1, "net_return_pct": 4.0}],
            "accepted_n": 1, "realized_pnl": 140.0}
        audit = selection_difference_attribution(neutral, priority)
        self.assertEqual(audit["pnl_bridge_difference"], 70.0)
        self.assertEqual(audit["by_symbol_difference"]["AAA"], -70.0)
        self.assertEqual(audit["by_symbol_difference"]["BBB"], 140.0)
        self.assertEqual(audit["additional_cost_sensitivity_bps"]["50"], 70.0)

    def test_pnl_bridge_reconciliation_fails_closed(self):
        neutral = {"accepted_signals": [], "accepted_n": 0, "realized_pnl": 0}
        priority = {"accepted_signals": [], "accepted_n": 0, "realized_pnl": 50}
        with self.assertRaisesRegex(ValueError, "PNL_BRIDGE_RECONCILIATION_FAILED"):
            selection_difference_attribution(neutral, priority)

    def test_reference_mismatch_blocks(self):
        with self.assertRaisesRegex(ValueError, "REFERENCE_RECONCILIATION_FAILED"):
            priority_experiment({"candidate_audit": [row("AAA", 1.0, 1.0)],
                                 "baseline": {"accepted_n": 0, "realized_pnl": 0},
                                 "filtered": {"accepted_n": 0, "realized_pnl": 0}})

    def test_missing_feature_blocks_only_affected_scenario(self):
        x = row("AAA", 0.0, 1.0)
        del x["features_at_signal_close"]["atr_14_pct"]
        result = priority_experiment({"candidate_audit": [x],
                                      "baseline": {"accepted_n": 1, "realized_pnl": 0},
                                      "filtered": {"accepted_n": 1, "realized_pnl": 0}})
        self.assertEqual(result["cohorts"]["baseline"]["scenarios"]["atr_low_first"]["status"],
                         "BLOCKED_MISSING_PREENTRY_FEATURE")

    def test_missing_reference_blocks(self):
        with self.assertRaisesRegex(ValueError, "MISSING_REFERENCE_PORTFOLIO"):
            priority_experiment({"candidate_audit": [], "baseline": {}, "filtered": {}})


if __name__ == "__main__":
    unittest.main()
