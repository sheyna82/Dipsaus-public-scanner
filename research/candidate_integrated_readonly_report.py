"""Read-only integration of existing candidate snapshot and evidence artifacts.

No new forecasts, broker connections or orders. Unknown evidence fails closed.
"""
import json
from pathlib import Path
import sys

# Reuse the already-tested root-level equity risk engine.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from research_swing_equity_risk import summarize_equity_curve

from candidate_decision_evidence_gate import assess
from candidate_portfolio_capacity import simulate


def build(snapshot, evidence_report, *, dated_signals=None, equity_observations=None):
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
        portfolio = simulate(dated_signals)
        portfolio["limitations"].append("Capacity is descriptive; dated signals must be independently validated and point-in-time eligible")
    if equity_observations is None:
        equity_risk = {"status": "NOT_EVALUATED", "reason": "DATED_EQUITY_MARKS_NOT_PROVIDED", "trade_ready": False}
    else:
        equity_risk = summarize_equity_curve(equity_observations)
        equity_risk["limitations"] = [
            "Observed close-to-close drawdown is not a forward stress forecast",
            "Caller must verify mark provenance, chronology, FX and cash reconciliation",
            "Not a live portfolio valuation or independent predictive validation",
        ]
    return {
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
