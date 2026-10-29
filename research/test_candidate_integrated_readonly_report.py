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
