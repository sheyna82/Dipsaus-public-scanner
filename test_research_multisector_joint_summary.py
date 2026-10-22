import unittest
from research_multisector_joint_summary import summarize, EXPECTED


def valid_row(symbol, sector):
    metric = {"events": 4, "mean_net_return_pct": 1.0}
    factor = {"selected": {"events": 2, "mean_net_return_pct": 2.0},
              "missed_winning_events": 1}
    return {"symbol": symbol, "sector": sector,
            "status": "EXPLORATORY_JOINT_FACTOR_DIAGNOSTIC",
            "baseline_test": metric,
            "dependence_diagnostic": {"test_signal_dates": ["2026-01-01", "2026-01-12", "2026-01-23", "2026-02-04"],
                "test_event_outcomes": [{"date": day, "net_return_pct": ret, "max_adverse_excursion_pct": -4.0,
                    "atr_structure_selected": chosen, "market_20d_positive": True,
                    "atr_expanding": chosen, "structure_above_20d_mean": True} for day, ret, chosen in
                    [("2026-01-01", 2.0, True), ("2026-01-12", 0.0, False),
                     ("2026-01-23", 2.0, True), ("2026-02-04", 0.0, False)]]},
            "market_regime_diagnostics": {
                "market_20d_positive": {"baseline": {"events": 4, "mean_net_return_pct": 1.0, "mean_adverse_excursion_pct": -5.0, "severe_adverse_rate_pct": 75.0},
                    "atr_structure_selected": {"events": 2, "winning_events": 1,
                        "mean_net_return_pct": 2.0, "mean_adverse_excursion_pct": -4.0,
                        "severe_adverse_rate_pct": 50.0},
                    "atr_structure_rejected": {"events": 2, "mean_net_return_pct": 0.0, "mean_adverse_excursion_pct": -6.0, "severe_adverse_rate_pct": 100.0}, "missed_winning_events": 1},
                "market_20d_nonpositive": {"baseline": None,
                    "atr_structure_selected": None, "atr_structure_rejected": None,
                    "missed_winning_events": 0}},
            "factors": {k: factor for k in ("atr_and_structure", "atr_and_market",
                                          "atr_structure_market")}}


class JointSummaryTests(unittest.TestCase):
    def test_valid_universe(self):
        rows = [valid_row(s, sector) for s, sector in EXPECTED.items()]
        result = summarize(rows)
        self.assertEqual(result["status"], "EXPLORATORY_SECTOR_REPLICATION_SUMMARY")
        self.assertEqual(result["symbols_evaluated"], 16)
        self.assertEqual(result["cross_symbol_dependence"]["same_day_cross_symbol_pairs"], 480)
        self.assertEqual(result["cross_symbol_dependence"]["signals_on_shared_days"], 64)
        self.assertEqual(result["cross_symbol_dependence"]["largest_same_day_cluster"], 16)
        self.assertEqual(result["cross_symbol_dependence"]["cross_day_pairs_within_14_calendar_days"], 768)
        self.assertEqual(result["cross_symbol_dependence"]["effective_days_kish_descriptive"], 4.0)
        self.assertEqual(result["comparisons"]["atr_and_structure"]["symbols_better"], 16)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["events"], 64)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["selected_events"], 32)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["selected_mean_net_return_pct"], 2.0)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["baseline_mean_net_return_pct"], 1.0)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["baseline_mean_adverse_excursion_pct"], -5.0)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["rejected_mean_net_return_pct"], 0.0)
        self.assertEqual(result["market_regime_summary"]["market_20d_positive"]["rejected_severe_adverse_rate_pct"], 100.0)
        self.assertEqual([x["offset_calendar_days"] for x in result["time_block_sensitivity"]["offset_sensitivity"]], [0, 3, 7, 10])
        self.assertEqual(result["time_block_sensitivity"]["all_offsets_positive"], all(
            x["mean_paired_block_delta_pct"] is not None and x["mean_paired_block_delta_pct"] > 0
            for x in result["time_block_sensitivity"]["offset_sensitivity"]))
        self.assertEqual(sum(x["events"] for x in result["chronological_era_sensitivity"]), 64)
        self.assertEqual(len(result["chronological_era_sensitivity"]), 3)
        self.assertEqual(len(result["chronological_era_symbol_coverage"]), 3)
        self.assertEqual(len(result["chronological_era_breadth"]), 3)
        self.assertEqual(len(result["chronological_era_market_regimes"]), 3)
        self.assertEqual(len(result["market_regime_cross_era_consistency"]), 2)
        self.assertEqual(len(result["chronological_era_factor_prevalence"]), 3)
        self.assertEqual(len(result["chronological_era_joint_factor_composition"]), 3)
        self.assertTrue(all(cell["severe_adverse_rate_pct"] == 100.0 for era in result["chronological_era_joint_factor_composition"] for cell in era["cells"] if cell["events"]))
        self.assertEqual(len(result["joint_factor_era_stability"]), 4)
        self.assertEqual(len(result["chronological_era_risk_return_tradeoff"]), 3)
        self.assertTrue(all(era["descriptive_only"] for era in result["chronological_era_risk_return_tradeoff"]))
        self.assertTrue(all(not x["predictive_edge_proven"] for x in result["joint_factor_era_stability"]))
        self.assertEqual(sum(cell["events"] for era in result["chronological_era_joint_factor_composition"] for cell in era["cells"]), 64)
        self.assertEqual(sum(x["factor_true_counts"]["atr_expanding"] for x in result["chronological_era_factor_prevalence"]), 32)
        self.assertFalse(result["market_regime_cross_era_consistency"][1]["all_three_eras_comparable"])
        self.assertEqual(sum(z["events"] for x in result["chronological_era_market_regimes"] for z in x["regimes"]), 64)
        self.assertTrue(all(x["comparable_symbols"] <= 16 for x in result["chronological_era_breadth"]))
        self.assertEqual(sum(x["symbols_with_both_groups"] for x in result["chronological_era_symbol_coverage"]), 16)
        self.assertFalse(result["chronological_era_stability"]["stable_across_eras_claimed"])
        self.assertEqual(result["chronological_era_stability"]["eras_positive"], sum(
            x["selected_minus_rejected_mean_pct"] is not None and x["selected_minus_rejected_mean_pct"] > 0
            for x in result["chronological_era_sensitivity"]))
        self.assertEqual(result["time_block_sensitivity"]["paired_blocks"], 1)
        self.assertEqual(result["time_block_sensitivity"]["selected_better_blocks"], 1)
        self.assertEqual(result["time_block_sensitivity"]["mean_paired_block_delta_pct"], 2.0)
        self.assertFalse(result["trade_ready"])

    def test_missing_symbol_blocks(self):
        rows = [valid_row(s, sector) for s, sector in list(EXPECTED.items())[:-1]]
        self.assertEqual(summarize(rows)["status"], "DATA_BLOCKED")

    def test_duplicate_blocks(self):
        rows = [valid_row(s, sector) for s, sector in EXPECTED.items()]
        self.assertEqual(summarize(rows + [rows[0]])["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
