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
        profit = result["reconciled_portfolio_research"]["closed_trade_profit_diagnostics"]
        self.assertEqual(profit["trade_count"], 1)
        self.assertEqual(profit["net_profit"], "70.00")
        efficiency = result["reconciled_portfolio_research"]["holding_capital_efficiency"]
        self.assertEqual(efficiency["completed_trades"], 1)
        self.assertEqual(efficiency["total_invested_tranche_sessions"], 2)
        self.assertEqual(efficiency["total_overnight_intervals"], 1)
        self.assertEqual(efficiency["capital_session_units"], "7000")
        self.assertEqual(efficiency["net_pnl_per_1000_currency_session_units"], "10.0000")
        self.assertEqual(profit["profit_factor"], "undefined_no_losses")
        self.assertFalse(profit["independent_real_trade_data_verified"])
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
            dated_signals=[{"symbol": "ABC", "entry_day": 0, "exit_day": 1, "net_return_pct": 2, "score": 1}]
        )
        self.assertTrue(timeline["cross_component_consistency"]["capacity_ledger_timeline_matched"])
        self.assertFalse(timeline["cross_component_consistency"]["portfolio_evidence_complete"])
        self.assertTrue(timeline["cross_component_consistency"]["capacity_ledger_net_returns_matched"])
        self.assertTrue(timeline["cross_component_consistency"]["selection_priority_equivalence_verified"])
        self.assertTrue(timeline["cross_component_consistency"]["capacity_ledger_rejected_identities_matched"])
        self.assertFalse(timeline["cross_component_consistency"]["transaction_cost_provenance_verified"])
        self.assertNotIn("SELECTION_PRIORITY_NOT_RECONCILED",
                         timeline["cross_component_consistency"]["blockers"])
        # Same accepted transaction but different source score must fail closed.
        with self.assertRaisesRegex(ValueError, "CAPACITY_LEDGER_SOURCE_POPULATION_MISMATCH"):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  dated_signals=[{"symbol": "ABC", "entry_day": 0, "exit_day": 1,
                                  "net_return_pct": 2, "score": 99}])
        # An extra rejected signal is still a population mismatch.
        with self.assertRaisesRegex(ValueError, "CAPACITY_LEDGER_SOURCE_POPULATION_MISMATCH"):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  dated_signals=[{"symbol": "ABC", "entry_day": 0, "exit_day": 1,
                                  "net_return_pct": 2, "score": 1},
                                 {"symbol": "ABC", "entry_day": 0, "exit_day": 1,
                                  "net_return_pct": 2, "score": 0}])
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  dated_signals=[{"symbol": "ABC", "entry_day": 0, "exit_day": 1,
                                  "net_return_pct": 3, "score": 1}])
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=inputs,
                  dated_signals=[{"symbol": "ABC", "entry_day": 1, "exit_day": 2, "net_return_pct": 2, "score": 1}])
        broken = {**inputs, "daily_marks": {}}
        with self.assertRaises(ValueError):
            build(snap, evidence, reconciled_portfolio_inputs=broken)

    def test_holding_efficiency_overlapping_trades_uses_trading_sessions(self):
        from datetime import date
        snap = {"research_only": True, "candidates": [
            {"symbol": "AAA", "decision": "WAIT", "blocks": []},
            {"symbol": "BBB", "decision": "WAIT", "blocks": []}]}
        evidence = {"research_only": True, "candidates": []}
        thu, fri, mon, tue = [date.fromisoformat(x) for x in
                              ("2026-10-01", "2026-10-02", "2026-10-05", "2026-10-06")]
        inputs = {
            "trades": [
                {"ticker": "AAA", "entry_date": thu, "exit_date": mon,
                 "net_return_pct": 2, "score": 10},
                {"ticker": "BBB", "entry_date": fri, "exit_date": tue,
                 "net_return_pct": -1, "score": 9},
            ],
            "daily_marks": {
                (thu, "AAA"): 3500,
                (fri, "AAA"): 3500, (fri, "BBB"): 3500,
                (mon, "BBB"): 3500,
            },
            "trading_dates": [thu, fri, mon, tue],
        }
        result = build(snap, evidence, reconciled_portfolio_inputs=inputs)
        reconciled = result["reconciled_portfolio_research"]
        holding = reconciled["holding_capital_efficiency"]
        profit = reconciled["closed_trade_profit_diagnostics"]
        self.assertEqual(holding["completed_trades"], 2)
        self.assertEqual(holding["total_invested_tranche_sessions"], 6)
        self.assertEqual(holding["total_overnight_intervals"], 4)
        self.assertEqual(holding["longest_holding_sessions"], 3)
        self.assertEqual(holding["capital_session_units"], "21000")
        self.assertEqual(profit["net_profit"], "35.00")
        self.assertEqual(holding["net_pnl_per_1000_currency_session_units"], "1.6667")
        self.assertFalse(result["trade_ready"])

    def test_competing_entries_match_ledger_score_priority(self):
        from datetime import date, timedelta
        from candidate_portfolio_capacity import simulate
        from research_swing_chronological_ledger import simulate_chronological_portfolio
        start = date(2026, 10, 1)
        end = start + timedelta(days=1)
        symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF", "ZZZ"]
        signals = [{"symbol": symbol, "entry_day": 0, "exit_day": 1,
                    "net_return_pct": 0, "score": 100 if symbol == "ZZZ" else 1}
                   for symbol in symbols]
        trades = [{"ticker": row["symbol"], "entry_date": start, "exit_date": end,
                   "net_return_pct": row["net_return_pct"], "score": row["score"]}
                  for row in signals]
        capacity = simulate(signals, priority_mode="score_desc")
        ledger = simulate_chronological_portfolio(trades)
        capacity_symbols = {row["symbol"] for row in capacity["accepted_signals"]}
        ledger_symbols = {row["ticker"] for row in ledger["ledger"]
                          if row["action"] == "entry"}
        self.assertEqual(capacity_symbols, ledger_symbols)
        self.assertEqual(capacity_symbols, set(symbols) - {"FFF"})
        self.assertEqual(capacity["rejected_n"], ledger["rejected_count"])
        self.assertEqual(capacity["realized_pnl"], 0)
        self.assertEqual(ledger["realized_net_pnl"], "0")
        self.assertEqual(simulate(signals)["accepted_signals"][-1]["symbol"], "FFF")
        with self.assertRaises(ValueError):
            simulate([{**signals[0], "score": float("nan")}],
                     priority_mode="score_desc")

    def test_ablation_portfolio_costs_and_liquidity_are_not_execution_verified(self):
        from candidate_portfolio_capacity import compare_ablation_portfolios
        from candidate_feature_ablation import FILTERS
        report = {"candidates": []}
        result = compare_ablation_portfolios(report, pattern="recovery_from_prior20_low_3to15pct")
        self.assertFalse(result["trade_ready"])
        self.assertTrue(result["costs_included_in_trade_returns"])
        assumptions = result["execution_cost_assumptions"]
        self.assertEqual(assumptions["roundtrip_fixed_cost_bps"], 50)
        self.assertEqual(assumptions["adverse_entry_slippage_bps"], 25)
        self.assertEqual(assumptions["entry_liquidity_filter"], "signal_session_close_times_volume")
        self.assertTrue(assumptions["point_in_time_liquidity_input"])
        self.assertFalse(assumptions["point_in_time_executable"])
        self.assertFalse(assumptions["independent_cost_provenance_verified"])
        self.assertEqual(set(result["comparison"]), set(FILTERS))

    def test_paired_liquidity_portfolios_compare_same_calendar(self):
        from candidate_portfolio_capacity import compare_ablation_portfolios
        from candidate_feature_ablation import FILTERS
        pattern = "recovery_from_prior20_low_3to15pct"
        current = {"entry_day": 1, "exit_day": 3, "net_return_pct": 2}
        legacy = {"entry_day": 1, "exit_day": 3, "net_return_pct": -1}
        detail = {"status": "DESCRIPTIVE_ONLY",
                  "portfolio_events_25bps": {"baseline": [current]},
                  "legacy_retrospective_portfolio_events_25bps": {"baseline": [legacy]}}
        report = {"candidates": [{"symbol": "ABC", "patterns": {pattern: detail}}]}
        result = compare_ablation_portfolios(report, pattern=pattern)
        pair = result["paired_liquidity_portfolios"]["baseline"]
        self.assertEqual(pair["point_in_time_event_n"], 1)
        self.assertEqual(pair["legacy_retrospective_event_n"], 1)
        self.assertEqual(pair["point_in_time"]["realized_pnl"], 70)
        self.assertEqual(pair["legacy_retrospective"]["realized_pnl"], -35)
        self.assertEqual(pair["realized_pnl_difference"], 105)
        self.assertTrue(pair["historical_comparison_only"])
        self.assertEqual(set(result["paired_liquidity_portfolios"]), set(FILTERS))

    def test_repeated_entries_cash_and_score_parity(self):
        from datetime import date, timedelta
        from candidate_portfolio_capacity import simulate
        from research_swing_chronological_ledger import simulate_chronological_portfolio
        origin = date(2026, 10, 1)
        rows = [
            ("AAA", 0, 3, 1, 10),
            ("BBB", 0, 2, 2, 9),
            ("CCC", 0, 2, 3, 8),
            ("DDD", 0, 2, 4, 7),
            ("EEE", 0, 2, 5, 6),
            ("FFF", 0, 2, 6, 5),
            ("ZZZ", 0, 2, 7, 100),
            ("AAA", 1, 4, 8, 99),
            ("GGG", 2, 4, 9, 101),
            ("HHH", 3, 5, 10, 102),
        ]
        signals = [{"symbol": s, "entry_day": entry, "exit_day": leave,
                    "net_return_pct": ret, "score": score}
                   for s, entry, leave, ret, score in rows]
        trades = [{"ticker": s, "entry_date": origin + timedelta(days=entry),
                   "exit_date": origin + timedelta(days=leave),
                   "net_return_pct": ret, "score": score}
                  for s, entry, leave, ret, score in rows]
        capacity = simulate(signals, priority_mode="score_desc")
        ledger = simulate_chronological_portfolio(trades)
        capacity_accepted = sorted((r["symbol"], r["entry_day"], r["exit_day"])
                                   for r in capacity["accepted_signals"])
        ledger_accepted = sorted(
            (r["ticker"], (date.fromisoformat(r["date"]) - origin).days)
            for r in ledger["ledger"] if r["action"] == "entry")
        self.assertEqual([(s, day) for s, day, _ in capacity_accepted], ledger_accepted)
        self.assertEqual(capacity["rejected_n"], ledger["rejected_count"])
        reasons = {"SYMBOL_ALREADY_HELD": "already_held",
                   "CAPACITY_FULL": "position_cap",
                   "INSUFFICIENT_CASH": "insufficient_cash"}
        rejected_capacity = sorted(
            (row["symbol"], (origin + timedelta(days=row["entry_day"])).isoformat(),
             reasons[row["reason"]]) for row in capacity["rejected_signals"])
        rejected_ledger = sorted(
            (row["ticker"], row["date"], row["reason"])
            for row in ledger["rejected_entries"])
        self.assertEqual(rejected_capacity, rejected_ledger)
        self.assertEqual(capacity["accepted_n"], len(ledger_accepted))
        self.assertAlmostEqual(capacity["realized_pnl"],
                               float(ledger["realized_net_pnl"]), places=2)
        self.assertEqual(capacity["rejection_reasons"]["SYMBOL_ALREADY_HELD"], 1)
        self.assertGreater(capacity["rejection_reasons"]["CAPACITY_FULL"], 0)

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
