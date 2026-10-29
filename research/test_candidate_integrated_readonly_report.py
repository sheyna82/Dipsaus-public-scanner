import unittest
from candidate_integrated_readonly_report import build


class IntegratedReadonlyTests(unittest.TestCase):
    def test_missing_data_and_forecasts_block(self):
        snapshot = {"research_only": True, "candidates": [
            {"symbol": "ABC", "decision": "WAIT", "blocks": ["EVENT_CALENDAR_UNVERIFIED"], "last_close": 12.0},
            {"symbol": "XYZ", "decision": "DATA_BLOCKED", "blocks": ["PRICE_DATA_UNAVAILABLE"]},
        ]}
        evidence = {"research_only": True, "candidates": [
            {"symbol": "ABC", "descriptive_median_excess_pct": 5.0, "descriptive_only": True}
        ]}
        result = build(snapshot, evidence)
        a, b = result["candidates"]
        self.assertFalse(a["trade_ready"])
        self.assertFalse(a["automatic_orders"])
        self.assertIsNone(a["independently_validated_estimates"]["expected_net_return_pct"])
        self.assertIn("EVENT_CALENDAR_UNVERIFIED", a["blockers"])
        self.assertEqual(a["descriptive_evidence_rows"], 1)
        self.assertIn("NO_MATCHING_DESCRIPTIVE_EVIDENCE", b["blockers"])
        self.assertIn("PRICE_DATA_UNAVAILABLE", b["blockers"])
        self.assertEqual(a["portfolio_capacity"], "NOT_EVALUATED_WITHOUT_DATED_ELIGIBLE_SIGNALS")
        self.assertEqual(result["portfolio_capacity_simulation"]["status"], "NOT_EVALUATED")
        self.assertEqual(result["portfolio_equity_risk"]["status"], "NOT_EVALUATED")

    def test_no_trade_ready_from_forged_evidence(self):
        snap = {"research_only": True, "candidates": [{"symbol": "ABC", "decision": "BUY", "blocks": []}]}
        evidence = {"research_only": True, "candidates": [
            {"symbol": "ABC", "trade_ready": True, "validated_win_probability": 0.99}
        ]}
        row = build(snap, evidence)["candidates"][0]
        self.assertFalse(row["trade_ready"])
        self.assertIn("UNRECOGNIZED_OR_UNSAFE_SNAPSHOT_DECISION", row["blockers"])
        self.assertIsNone(row["independently_validated_estimates"]["validated_win_probability"])

    def test_reuses_existing_chronological_capacity_simulator(self):
        snapshot = {"research_only": True, "candidates": [{"symbol": "ABC", "decision": "WAIT", "blocks": []}]}
        evidence = {"research_only": True, "candidates": []}
        signals = [{"symbol": "ABC", "entry_day": 1, "exit_day": 6, "net_return_pct": 2.0}]
        result = build(snapshot, evidence, dated_signals=signals)
        portfolio = result["portfolio_capacity_simulation"]
        self.assertEqual(portfolio["accepted_n"], 1)
        self.assertEqual(portfolio["realized_pnl"], 70.0)
        self.assertFalse(portfolio["trade_ready"])
        self.assertFalse(result["trade_ready"])
        with self.assertRaises(ValueError):
            build(snapshot, evidence, dated_signals=[{"symbol": "OTHER", "entry_day": 1, "exit_day": 6, "net_return_pct": 2}])

    def test_reuses_existing_equity_drawdown_engine(self):
        snap = {"research_only": True, "candidates": [{"symbol": "ABC", "decision": "WAIT", "blocks": []}]}
        evidence = {"research_only": True, "candidates": []}
        marks = [{"date": "2026-10-01", "equity": 21000},
                 {"date": "2026-10-02", "equity": 18900},
                 {"date": "2026-10-05", "equity": 20500}]
        result = build(snap, evidence, equity_observations=marks)
        risk = result["portfolio_equity_risk"]
        self.assertEqual(risk["max_observed_drawdown_pct"], "10.0000")
        self.assertFalse(risk["trade_ready"])
        self.assertFalse(result["trade_ready"])
        with self.assertRaises(ValueError):
            build(snap, evidence, equity_observations=list(reversed(marks)))

    def test_sector_concentration_and_capital_duration(self):
        snap = {"research_only": True, "candidates": [
            {"symbol": "ABC", "decision": "WAIT", "blocks": []},
            {"symbol": "DEF", "decision": "WAIT", "blocks": []}
        ]}
        evidence = {"research_only": True, "candidates": []}
        signals = [
            {"symbol": "ABC", "entry_day": 1, "exit_day": 7, "net_return_pct": 1},
            {"symbol": "DEF", "entry_day": 2, "exit_day": 9, "net_return_pct": -1}
        ]
        result = build(snap, evidence, dated_signals=signals,
                       sector_by_symbol={"ABC": "Technology", "DEF": "Technology"})
        concentration = result["portfolio_concentration"]
        self.assertEqual(concentration["peak_same_sector_positions"], 2)
        self.assertEqual(concentration["peak_sector_positions"]["Technology"], 2)
        self.assertEqual(concentration["max_holding_day_units"], 7)
        self.assertFalse(concentration["trade_ready"])
        with self.assertRaises(ValueError):
            build(snap, evidence, dated_signals=signals, sector_by_symbol={"ABC": "Technology"})

    def test_cross_component_does_not_claim_reconciliation(self):
        snap = {"research_only": True, "candidates": [
            {"symbol": "ABC", "decision": "WAIT", "blocks": []}
        ]}
        evidence = {"research_only": True, "candidates": []}
        result = build(
            snap, evidence,
            dated_signals=[{"symbol": "ABC", "entry_day": 1, "exit_day": 3, "net_return_pct": 1}],
            sector_by_symbol={"ABC": "Technology"},
            equity_observations=[{"date": "2026-10-01", "equity": 21000},
                                 {"date": "2026-10-02", "equity": 25000}]
        )
        gate = result["cross_component_consistency"]
        self.assertTrue(gate["capacity_available"])
        self.assertTrue(gate["sector_exposure_available"])
        self.assertTrue(gate["equity_risk_available"])
        self.assertFalse(gate["cash_equity_reconciled"])
        self.assertFalse(gate["portfolio_evidence_complete"])
        self.assertFalse(gate["trade_ready"])
        self.assertIn("PORTFOLIO_METRICS_NOT_SAME_COHORT_VERIFIED", gate["blockers"])

    def test_arithmetic_reconciliation_is_not_source_verification(self):
        from datetime import date
        snap = {"research_only": True, "candidates": [{"symbol": "ABC", "decision": "WAIT", "blocks": []}]}
        evidence = {"research_only": True, "candidates": []}
        inputs = {
            "trades": [{"ticker": "ABC", "entry_date": date(2026, 10, 1),
                        "exit_date": date(2026, 10, 2), "net_return_pct": 2, "score": 1}],
            "daily_marks": {(date(2026, 10, 1), "ABC"): 3500},
            "trading_dates": [date(2026, 10, 1), date(2026, 10, 2)]
        }
        result = build(snap, evidence, reconciled_portfolio_inputs=inputs)
        self.assertTrue(result["cross_component_consistency"]["cash_equity_reconciled"])
        self.assertFalse(result["cross_component_consistency"]["portfolio_evidence_complete"])
        self.assertFalse(result["reconciled_portfolio_research"]["independent_provenance_verified"])
        self.assertFalse(result["trade_ready"])
        aligned = [{"date": "2026-10-01", "equity": 21000},
                   {"date": "2026-10-02", "equity": 21070}]
        aligned_result = build(snap, evidence, reconciled_portfolio_inputs=inputs,
                               equity_observations=aligned)
        self.assertTrue(aligned_result["cross_component_consistency"]["equity_series_matched_to_reconciled_ledger"])
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  equity_observations=[{"date": "2026-10-01", "equity": 21000},
                                       {"date": "2026-10-02", "equity": 22000}])
        timeline = build(
            snap, evidence, reconciled_portfolio_inputs=inputs,
            dated_signals=[{"symbol": "ABC", "entry_day": 0, "exit_day": 1, "net_return_pct": 2}]
        )
        self.assertTrue(timeline["cross_component_consistency"]["capacity_ledger_timeline_matched"])
        self.assertFalse(timeline["cross_component_consistency"]["portfolio_evidence_complete"])
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  dated_signals=[{"symbol": "ABC", "entry_day": 1, "exit_day": 2, "net_return_pct": 2}])
        broken = {**inputs, "daily_marks": {}}
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=broken)

    def test_malformed_blockers_fail_closed(self):
        evidence = {"research_only": True, "candidates": []}
        for blockers in ("NOT_A_LIST", [None], [123]):
            snapshot = {"research_only": True, "candidates": [
                {"symbol": "ABC", "decision": "WAIT", "blocks": blockers}
            ]}
            with self.assertRaises(ValueError):
                build(snapshot, evidence)

    def test_invalid_inputs_and_duplicate_symbols(self):
        with self.assertRaises(ValueError):
            build({"candidates": []}, {"research_only": True, "candidates": []})
        with self.assertRaises(ValueError):
            build({"research_only": True, "candidates": [{"symbol": "ABC"}, {"symbol": "ABC"}]},
                  {"research_only": True, "candidates": []})


if __name__ == "__main__":
    unittest.main()
