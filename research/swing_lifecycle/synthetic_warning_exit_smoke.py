"""Deterministic offline smoke benchmark; synthetic prices, NOT market history.

Exercises the complete warning -> exit -> chronological ledger -> purged holdout
pipeline with both adverse and rebound outcomes. No trading functionality.
"""
from datetime import date, timedelta
import json
from research.swing_lifecycle.warning_exit_holdout import evaluate_warning_exit_holdout


def _scenario(ticker, start, outcome):
    bars = []
    for i in range(32):
        d = start + timedelta(days=i)
        bars.append({"date": d.isoformat(), "open": 100.0,
                     "high": 101.0, "low": 99.0, "close": 100.0})
    bars[24].update(open=94.0, high=95.0, low=90.0, close=91.0)
    bars[25].update(open=89.0, high=91.0, low=88.0, close=90.0)
    last = 80.0 if outcome == "decline" else 120.0
    bars[29].update(open=last, high=last + 2, low=last - 1, close=last + 1)
    return {"ticker": ticker, "bars": bars,
            "entry_index": 21, "baseline_exit_index": 29, "score": 10}


def synthetic_warning_exit_smoke_report():
    cases = [
        _scenario("OLD_DECLINE", date(2025, 1, 1), "decline"),
        _scenario("OLD_REBOUND", date(2025, 3, 1), "rebound"),
        _scenario("NEW_DECLINE", date(2026, 1, 1), "decline"),
        _scenario("NEW_REBOUND", date(2026, 3, 1), "rebound"),
    ]
    result = evaluate_warning_exit_holdout(
        cases, cutoff=date(2025, 8, 1), embargo_days=15,
        cost_bps_per_side=10)
    return {
        "dataset": "synthetic_not_historical",
        "scenarios": len(cases),
        "result": result,
        "research_only": True,
        "historical_edge_proven": False,
    }


if __name__ == "__main__":
    print(json.dumps(synthetic_warning_exit_smoke_report(),
                     indent=2, sort_keys=True))
