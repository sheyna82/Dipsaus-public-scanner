"""Read-only integration of existing candidate snapshot and evidence artifacts.

No new forecasts, broker connections or orders. Unknown evidence fails closed.
"""
import json
from pathlib import Path
import sys

# Reuse the already-tested root-level equity risk engine.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_swing_equity_risk import summarize_equity_curve
from research_swing_portfolio_with_marks import backtest_portfolio_with_marks
from research_swing_closed_trade_profit_diagnostics import analyze_closed_trade_pnl

from candidate_decision_evidence_gate import assess
from candidate_portfolio_capacity import simulate



def concentration_from_accepted(portfolio, sectors):
    """Descriptive peak sector occupancy for actually accepted simulated trades."""
    if not isinstance(sectors, dict):
        raise ValueError("INVALID_SECTOR_MAPPING")
    accepted = portfolio["accepted_signals"]
    for row in accepted:
        if not isinstance(sectors.get(row["symbol"]), str) or not sectors[row["symbol"]].strip():
            raise ValueError("MISSING_SECTOR_FOR_ACCEPTED_SIGNAL")
    if not accepted:
        return {"status": "NO_ACCEPTED_TRADES", "trade_ready": False, "peak_sector_positions": {},
                "peak_same_sector_positions": 0, "max_holding_day_units": 0}
    days = sorted({day for row in accepted for day in range(row["entry_day"], row["exit_day"])})
    peak = {}
    max_same = 0
    for day in days:
        counts = {}
        for row in accepted:
            if row["entry_day"] <= day < row["exit_day"]:
                sector = sectors[row["symbol"]].strip()
                counts[sector] = counts.get(sector, 0) + 1
        for sector, count in counts.items():
            peak[sector] = max(peak.get(sector, 0), count)
            max_same = max(max_same, count)
    return {"status": "DESCRIPTIVE_ACCEPTED_TRADE_EXPOSURE", "trade_ready": False,
            "peak_sector_positions": dict(sorted(peak.items())),
            "peak_same_sector_positions": max_same,
            "max_holding_day_units": max(row["exit_day"] - row["entry_day"] for row in accepted),
            "limitations": ["Entry/exit integer days are not verified exchange sessions",
                            "Sector labels are caller supplied, not independently verified",
                            "No price correlation, FX, intraday exposure or live risk prediction"]}

def build(snapshot, evidence_report, *, dated_signals=None, equity_observations=None, sector_by_symbol=None, reconciled_portfolio_inputs=None):
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("candidates"), list):
        raise ValueError("INVALID_SNAPSHOT")
    if not isinstance(evidence_report, dict) or not isinstance(evidence_report.get("candidates"), list):
        raise ValueError("INVALID_EVIDENCE_REPORT")
    if snapshot.get("research_only") is not True or evidence_report.get("research_only") is not True:
        raise ValueError("RESEARCH_ONLY_SOURCE_REQUIRED")
    evidence_by_symbol = {}
    for row in evidence_report["candidates"]:
        if not isinstance(row, dict) or not isinstance(row.get("symbol"), str):
            raise ValueError("INVALID_EVIDENCE_ROW")
        evidence_by_symbol.setdefault(row["symbol"], []).append(row)
    output = []
    seen = set()
    for snap in snapshot["candidates"]:
        if not isinstance(snap, dict) or not isinstance(snap.get("symbol"), str) or not snap["symbol"].strip():
            raise ValueError("INVALID_SNAPSHOT_ROW")
        symbol = snap["symbol"].strip()
        if symbol in seen:
            raise ValueError("DUPLICATE_SNAPSHOT_SYMBOL")
        seen.add(symbol)
        # Deliberately do not promote descriptive cohort metrics to forecasts.
        gate = assess({"symbol": symbol})
        raw_blocks = snap.get("blocks", [])
        if not isinstance(raw_blocks, list) or any(not isinstance(item, str) or not item for item in raw_blocks):
            raise ValueError("INVALID_SNAPSHOT_BLOCKERS")
        blockers = list(dict.fromkeys([*raw_blocks, *gate["missing_or_failed_gates"]]))
        if snap.get("decision") not in ("WAIT", "DATA_BLOCKED"):
            blockers.append("UNRECOGNIZED_OR_UNSAFE_SNAPSHOT_DECISION")
        if snap.get("decision") == "DATA_BLOCKED":
            blockers.append("PRICE_DATA_UNAVAILABLE")
        if not evidence_by_symbol.get(symbol):
            blockers.append("NO_MATCHING_DESCRIPTIVE_EVIDENCE")
        output.append({
            "symbol": symbol,
            "status": "RESEARCH_ONLY_NOT_TRADE_READY",
            "trade_ready": False,
            "automatic_orders": False,
            "manual_decision_required": True,
            "snapshot_decision": snap.get("decision"),
            "last_bar_utc": snap.get("last_bar_utc"),
            "last_close": snap.get("last_close"),
            "snapshot_source": snap.get("source"),
            "descriptive_evidence_rows": len(evidence_by_symbol.get(symbol, [])),
            "independently_validated_estimates": gate["estimates"],
            "blockers": list(dict.fromkeys(blockers)),
            "portfolio_capacity": "NOT_EVALUATED_WITHOUT_DATED_ELIGIBLE_SIGNALS",
            "limitations": [
                "Snapshot quote is not a verified executable bid/ask",
                "Descriptive historical cohorts are not calibrated predictions",
                "No broker fees, FX, sector risk or live fill verification",
                "No portfolio-capacity inference without independently dated eligible signals",
            ],
        })
    if dated_signals is None:
        portfolio = {"status": "NOT_EVALUATED", "reason": "DATED_SIGNALS_NOT_PROVIDED", "trade_ready": False}
    else:
        if not isinstance(dated_signals, list):
            raise ValueError("INVALID_DATED_SIGNALS")
        allowed = set(seen)
        if any(not isinstance(row, dict) or row.get("symbol") not in allowed for row in dated_signals):
            raise ValueError("SIGNAL_NOT_IN_CANDIDATE_SNAPSHOT")
        shared_selection = reconciled_portfolio_inputs is not None
        if shared_selection and any(not isinstance(row.get("score"), (int, float)) or isinstance(row.get("score"), bool) for row in dated_signals):
            raise ValueError("SHARED_SELECTION_REQUIRES_NUMERIC_SCORES")
        portfolio = simulate(dated_signals, priority_mode="score_desc" if shared_selection else "symbol_asc")
        portfolio["limitations"].append("Capacity is descriptive; dated signals must be independently validated and point-in-time eligible")
    if dated_signals is None or sector_by_symbol is None:
        concentration = {"status": "NOT_EVALUATED", "reason": "DATED_SIGNALS_AND_SECTOR_MAPPING_REQUIRED", "trade_ready": False}
    else:
        concentration = concentration_from_accepted(portfolio, sector_by_symbol)
    if equity_observations is None:
        equity_risk = {"status": "NOT_EVALUATED", "reason": "DATED_EQUITY_MARKS_NOT_PROVIDED", "trade_ready": False}
    else:
        equity_risk = summarize_equity_curve(equity_observations)
        equity_risk["limitations"] = [
            "Observed close-to-close drawdown is not a forward stress forecast",
            "Caller must verify mark provenance, chronology, FX and cash reconciliation",
            "Not a live portfolio valuation or independent predictive validation",
        ]
    if reconciled_portfolio_inputs is None:
        reconciled = {"status": "NOT_EVALUATED", "reason": "AUDITABLE_FILLS_MARKS_AND_DATES_NOT_PROVIDED", "trade_ready": False}
    else:
        if not isinstance(reconciled_portfolio_inputs, dict) or set(reconciled_portfolio_inputs) != {"trades", "daily_marks", "trading_dates"}:
            raise ValueError("INVALID_RECONCILIATION_INPUTS")
        verified = backtest_portfolio_with_marks(**reconciled_portfolio_inputs)
        if equity_observations is not None:
            reconciled_curve = verified["equity"]["equity_curve"]
            supplied = [(row["date"], str(row["equity"])) for row in equity_observations]
            from decimal import Decimal
            try:
                matches = len(supplied) == len(reconciled_curve) and all(
                    supplied[i][0] == reconciled_curve[i]["date"] and
                    Decimal(supplied[i][1]) == Decimal(reconciled_curve[i]["equity"])
                    for i in range(len(supplied))
                )
            except (KeyError, TypeError, ValueError, ArithmeticError):
                matches = False
            if not matches:
                raise ValueError("EQUITY_SERIES_RECONCILIATION_MISMATCH")
        closed_trade_pnls = [row["net_pnl"] for row in verified["cash_accounting"]["ledger"]
                             if row["action"] == "exit"]
        closed_trade_diagnostics = (
            analyze_closed_trade_pnl(closed_trade_pnls) if closed_trade_pnls
            else {"status": "NO_COMPLETED_TRADES", "trade_ready": False}
        )
        if closed_trade_pnls:
            from decimal import Decimal
            if Decimal(closed_trade_diagnostics["net_profit"]) != Decimal(
                    verified["cash_accounting"]["realized_net_pnl"]).quantize(Decimal("0.01")):
                raise ValueError("CLOSED_TRADE_PNL_RECONCILIATION_MISMATCH")
        from datetime import date
        from decimal import Decimal
        open_by_symbol = {}
        holding_sessions = []
        holding_overnight_intervals = []
        for event in verified["cash_accounting"]["ledger"]:
            symbol = event["ticker"]
            if event["action"] == "entry":
                if symbol in open_by_symbol:
                    raise ValueError("AMBIGUOUS_HOLDING_PERIOD")
                open_by_symbol[symbol] = date.fromisoformat(event["date"])
            elif event["action"] == "exit":
                if symbol not in open_by_symbol:
                    raise ValueError("AMBIGUOUS_HOLDING_PERIOD")
                start = open_by_symbol.pop(symbol)
                finish = date.fromisoformat(event["date"])
                sessions = sum(start <= day <= finish for day in reconciled_portfolio_inputs["trading_dates"])
                overnight_intervals = sum(start <= day < finish for day in reconciled_portfolio_inputs["trading_dates"])
                if sessions < 1:
                    raise ValueError("INVALID_HOLDING_SESSION_COUNT")
                holding_sessions.append(sessions)
                holding_overnight_intervals.append(overnight_intervals)
        if open_by_symbol:
            raise ValueError("UNCLOSED_HOLDING_PERIOD")
        capital_session_units = sum(Decimal("3500") * n for n in holding_sessions)
        holding_efficiency = {
            "status": "DESCRIPTIVE_COMPLETED_TRADES" if holding_sessions else "NO_COMPLETED_TRADES",
            "trade_ready": False,
            "completed_trades": len(holding_sessions),
            "total_invested_tranche_sessions": sum(holding_sessions),
            "total_overnight_intervals": sum(holding_overnight_intervals),
            "session_definition": "Inclusive entry and exit trading sessions; entry at open and exit at close",
            "capital_session_units": str(capital_session_units),
            "longest_holding_sessions": max(holding_sessions, default=0),
            "net_pnl_per_1000_currency_session_units": (
                str((Decimal(verified["cash_accounting"]["realized_net_pnl"]) /
                     capital_session_units * 1000).quantize(Decimal("0.0001")))
                if capital_session_units else None),
            "limitations": [
                "Capital-session efficiency is descriptive, not an annualized return or a forecast",
                "Uses the research ledger fixed tranche of 3500 and caller-supplied session calendar",
                "Exit session included in occupied sessions; overnight intervals separately reported",
                "No intraday capital usage, financing, FX or broker fill verification",
            ],
        }
        reconciled = {"status": "ARITHMETIC_RECONCILED_RESEARCH_ONLY",
                      "cash_equity_reconciliation": verified["cash_equity_reconciliation"],
                      "equity": verified["equity"],
                      "closed_trade_profit_diagnostics": closed_trade_diagnostics,
                      "holding_capital_efficiency": holding_efficiency,
                      "trade_ready": False,
                      "independent_provenance_verified": False,
                      "limitations": ["Arithmetic reconciliation is not source authentication",
                                      "No verified matching to separate integer-day capacity simulation",
                                      "No broker execution, FX or corporate-action attestation"]}
    timeline_match = False
    if dated_signals is not None and reconciled_portfolio_inputs is not None:
        from datetime import date
        dates = reconciled_portfolio_inputs["trading_dates"]
        if any(type(day) is not date for day in dates) or dates != sorted(set(dates)):
            raise ValueError("INVALID_SHARED_TRADING_CALENDAR")
        accepted = portfolio["accepted_signals"]
        if any(row["entry_day"] < 0 or row["exit_day"] >= len(dates) for row in accepted):
            raise ValueError("CAPACITY_DAY_OUTSIDE_SHARED_CALENDAR")
        capacity_keys = sorted((row["symbol"], dates[row["entry_day"]], dates[row["exit_day"]])
                               for row in accepted)
        ledger = verified["cash_accounting"]["ledger"]
        active = {}
        ledger_keys = []
        for event in ledger:
            key = event["ticker"]
            if event["action"] == "entry":
                if key in active:
                    raise ValueError("AMBIGUOUS_LEDGER_TRADE_PAIRING")
                active[key] = event["date"]
            elif event["action"] == "exit":
                if key not in active:
                    raise ValueError("AMBIGUOUS_LEDGER_TRADE_PAIRING")
                ledger_keys.append((key, date.fromisoformat(active.pop(key)),
                                    date.fromisoformat(event["date"])))
        if active or sorted(capacity_keys) != sorted(ledger_keys):
            raise ValueError("CAPACITY_LEDGER_TIMELINE_MISMATCH")
        from decimal import Decimal
        accepted_keys = {(row["symbol"], row["entry_day"], row["exit_day"]) for row in accepted}
        capacity_returns = sorted((row["symbol"], dates[row["entry_day"]],
                                   dates[row["exit_day"]], Decimal(str(row["net_return_pct"])))
                                  for row in dated_signals
                                  if (row["symbol"], row["entry_day"], row["exit_day"]) in accepted_keys)
        ledger_returns = sorted((row["ticker"], row["entry_date"], row["exit_date"],
                                 Decimal(str(row["net_return_pct"])))
                                for row in reconciled_portfolio_inputs["trades"]
                                if (row["ticker"], row["entry_date"], row["exit_date"]) in ledger_keys)
        if capacity_returns != ledger_returns:
            raise ValueError("CAPACITY_LEDGER_RETURN_MISMATCH")
        # Selection ordering is not interchangeable: the ledger uses score DESC,
        # while capacity defaults to symbol ASC and optional priority ASC.
        # Matching accepted trades alone does not prove matching rejected entries.
        capacity_rejections = portfolio["rejected_n"]
        ledger_rejections = verified["cash_accounting"]["rejected_count"]
        if capacity_rejections != ledger_rejections:
            raise ValueError("CAPACITY_LEDGER_REJECTION_COUNT_MISMATCH")
        reason_map = {"SYMBOL_ALREADY_HELD": "already_held",
                      "CAPACITY_FULL": "position_cap",
                      "INSUFFICIENT_CASH": "insufficient_cash"}
        if any(row["entry_day"] < 0 or row["entry_day"] >= len(dates)
               for row in portfolio["rejected_signals"]):
            raise ValueError("REJECTED_DAY_OUTSIDE_SHARED_CALENDAR")
        capacity_rejected_keys = sorted(
            (row["symbol"], dates[row["entry_day"]].isoformat(), reason_map[row["reason"]])
            for row in portfolio["rejected_signals"])
        ledger_rejected_keys = sorted(
            (row["ticker"], row["date"], row["reason"])
            for row in verified["cash_accounting"]["rejected_entries"])
        if capacity_rejected_keys != ledger_rejected_keys:
            raise ValueError("CAPACITY_LEDGER_REJECTION_IDENTITY_MISMATCH")
        if abs(Decimal(str(portfolio["realized_pnl"])) -
               Decimal(verified["cash_accounting"]["realized_net_pnl"])) > Decimal("0.011"):
            raise ValueError("CAPACITY_LEDGER_PNL_MISMATCH")
        timeline_match = True
    checks = {
        "research_only": True,
        "trade_ready": False,
        "capacity_available": portfolio.get("status") == "DESCRIPTIVE_PORTFOLIO_SIMULATION",
        "sector_exposure_available": concentration.get("status") == "DESCRIPTIVE_ACCEPTED_TRADE_EXPOSURE",
        "equity_risk_available": equity_risk.get("risk_estimate_type") == "sampled_portfolio_equity_only",
        "capacity_ledger_timeline_matched": timeline_match,
        "capacity_ledger_net_returns_matched": timeline_match,
        "capacity_ledger_rejected_identities_matched": timeline_match,
        "selection_priority_equivalence_verified": timeline_match and portfolio.get("priority_mode") == "score_desc",
        "transaction_cost_provenance_verified": False,
        "cash_equity_reconciled": reconciled.get("status") == "ARITHMETIC_RECONCILED_RESEARCH_ONLY",
        "signal_provenance_verified": False,
        "portfolio_evidence_complete": False,
        "equity_series_matched_to_reconciled_ledger": reconciled.get("status") == "ARITHMETIC_RECONCILED_RESEARCH_ONLY" and equity_observations is not None,
        "blockers": [
            "SIGNAL_PROVENANCE_NOT_INDEPENDENTLY_VERIFIED",
            "PORTFOLIO_METRICS_NOT_SAME_COHORT_VERIFIED",
            "TRANSACTION_COST_PROVENANCE_UNVERIFIED",
        ],
    }
    if not timeline_match:
        checks["blockers"].append("CAPACITY_LEDGER_TIMELINE_NOT_MATCHED")
    if not checks["selection_priority_equivalence_verified"]:
        checks["blockers"].append("SELECTION_PRIORITY_NOT_RECONCILED")
    if not checks["cash_equity_reconciled"]:
        checks["blockers"].append("CASH_EQUITY_RECONCILIATION_NOT_PROVIDED")
    if not checks["equity_series_matched_to_reconciled_ledger"]:
        checks["blockers"].append("EQUITY_SERIES_NOT_MATCHED_TO_LEDGER")
    if not checks["capacity_available"]:
        checks["blockers"].append("CAPACITY_NOT_EVALUATED")
    if not checks["sector_exposure_available"]:
        checks["blockers"].append("SECTOR_EXPOSURE_NOT_EVALUATED")
    if not checks["equity_risk_available"]:
        checks["blockers"].append("EQUITY_RISK_NOT_EVALUATED")
    return {
        "reconciled_portfolio_research": reconciled,
        "cross_component_consistency": checks,
        "portfolio_concentration": concentration,
        "portfolio_equity_risk": equity_risk,
        "portfolio_capacity_simulation": portfolio,
        "research_only": True, "trade_ready": False, "automatic_orders": False,
        "source_artifacts": ["candidate_entry_research.json", "candidate_decision_evidence.json"],
        "candidates": output,
    }


def main():
    source_dir = Path("reports")
    snapshot = json.loads((source_dir / "candidate_entry_research.json").read_text(encoding="utf-8"))
    evidence = json.loads((source_dir / "candidate_decision_evidence.json").read_text(encoding="utf-8"))
    result = build(snapshot, evidence)
    target = source_dir / "candidate_integrated_readonly.json"
    target.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"status": "RESEARCH_ONLY", "candidates": len(result["candidates"])}))


if __name__ == "__main__":
    main()
