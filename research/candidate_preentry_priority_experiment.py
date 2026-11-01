"""Predeclared, research-only candidate priority stress test.

Scores use signal-close feature values only. No historical outcome enters scoring.
This is an exploratory sensitivity test on an already inspected historical sample,
not evidence of predictive skill or a trade recommendation.
"""
import math
from datetime import datetime, timezone
from collections import defaultdict


def entry_quarter_attribution(simulation, tranche=3500.0):
    """Attribute realized trade PnL to entry quarter; NOT a quarterly equity return."""
    buckets = defaultdict(list)
    for trade in simulation['accepted_signals']:
        day = datetime.fromtimestamp(trade['entry_day'] * 86400, tz=timezone.utc)
        quarter = f'{day.year}Q{(day.month - 1)//3 + 1}'
        buckets[quarter].append(trade['net_return_pct'] * tranche / 100)
    return {q: {'trades_n': len(values), 'entry_attributed_pnl': round(sum(values), 2),
                'positive_trade_n': sum(v > 0 for v in values)}
            for q, values in sorted(buckets.items())}
from candidate_portfolio_capacity import simulate, calendar_capital_occupancy

# Fixed before reading outcomes. These are hypotheses, not optimized coefficients.
PRIORITIES = {
    "relative_strength_desc": ("relative_strength_20d_pct", 1),
    "relative_strength_asc": ("relative_strength_20d_pct", -1),
    "atr_low_first": ("atr_14_pct", -1),
    "volume_high_first": ("volume_ratio_20d", 1),
}


def selection_difference_attribution(neutral, selected, *, tranche=3500.0):
    """Reconcile descriptive trade-level PnL changes, not causal attribution."""
    a = {(r["symbol"], r["entry_day"]): r for r in neutral["accepted_signals"]}
    b = {(r["symbol"], r["entry_day"]): r for r in selected["accepted_signals"]}
    if len(a) != len(neutral["accepted_signals"]) or len(b) != len(selected["accepted_signals"]):
        raise ValueError("DUPLICATE_ACCEPTED_TRADE")
    deltas = {}
    for key in sorted(set(a) | set(b)):
        before, after = a.get(key), b.get(key)
        if before and after and abs(before["net_return_pct"] - after["net_return_pct"]) > 1e-8:
            raise ValueError("INCONSISTENT_SHARED_OUTCOME")
        delta = tranche * ((after["net_return_pct"] if after else 0) -
                           (before["net_return_pct"] if before else 0)) / 100
        if delta:
            deltas[key] = delta
    by_symbol = defaultdict(float)
    for (symbol, _), delta in deltas.items():
        by_symbol[symbol] += delta
    total = round(sum(deltas.values()), 2)
    if abs(total - (selected["realized_pnl"] - neutral["realized_pnl"])) > .03:
        raise ValueError("PNL_BRIDGE_RECONCILIATION_FAILED")
    return {
        "pnl_bridge_difference": total,
        "by_symbol_difference": {symbol: round(value, 2)
                                 for symbol, value in sorted(by_symbol.items())},
        "largest_absolute_single_event_difference": round(max((abs(v) for v in deltas.values()), default=0), 2),
        "largest_absolute_symbol_contribution": round(max((abs(v) for v in by_symbol.values()), default=0), 2),
        "event_difference_count": len(deltas),
        "additional_cost_sensitivity_bps": {
            str(bps): round(total - (selected["accepted_n"] - neutral["accepted_n"]) *
                            tranche * bps / 10000, 2)
            for bps in (10, 25, 50)
        },
        "limitations": [
            "Historical PnL bridge only, not a causal replacement or independent validation",
            "Additional costs are per accepted trade, not a spread/slippage fill simulation",
            "No change to trade selection under cost stress, no path-dependent cash replay"
        ]
    }


def volume_leave_one_symbol_out(events):
    """Exploratory leave-one-symbol-out capacity replay; no model selection."""
    symbols = sorted({e["symbol"] for e in events})
    output = {}
    for omitted in symbols:
        subset = [e for e in events if e["symbol"] != omitted]
        base = simulate([{k: v for k, v in e.items() if k != "features"} for e in subset])
        ranked = simulate([{k: v for k, v in e.items() if k != "features"} |
                           {"score": e["features"]["volume_ratio_20d"]}
                           for e in subset], priority_mode="score_desc")
        output[omitted] = {
            "neutral_accepted_n": base["accepted_n"],
            "volume_accepted_n": ranked["accepted_n"],
            "difference_eur": round(ranked["realized_pnl"] - base["realized_pnl"], 2)
        }
    return {
        "status": "EXPLORATORY_ONLY",
        "symbol_count": len(symbols),
        "omissions": output,
        "positive_count": sum(v["difference_eur"] > 0 for v in output.values()),
        "nonpositive_count": sum(v["difference_eur"] <= 0 for v in output.values()),
        "independent_validation": False,
        "trade_ready": False
    }


def priority_experiment(portfolio):
    rows = portfolio.get("candidate_audit")
    if not isinstance(rows, list):
        raise ValueError("MISSING_CANDIDATE_AUDIT")
    results = {}
    for cohort in ("baseline", "filtered"):
        eligible = [r for r in rows if cohort == "baseline" or r.get("filter_selected") is True]
        reference = portfolio.get(cohort, {})
        if reference.get("accepted_n") is None:
            raise ValueError("MISSING_REFERENCE_PORTFOLIO")
        baseline_events = []
        for row in eligible:
            f = row.get("features_at_signal_close")
            if not isinstance(f, dict):
                raise ValueError("MISSING_SIGNAL_CLOSE_FEATURES")
            ret = row.get("historical_net_return_pct_outcome_not_selection_input")
            if not isinstance(ret, (float, int)) or isinstance(ret, bool) or not math.isfinite(ret):
                raise ValueError("INVALID_HISTORICAL_OUTCOME")
            baseline_events.append({
                "symbol": row["symbol"], "entry_day": row["entry_day"],
                "exit_day": row["exit_day"], "net_return_pct": ret,
                "features": f
            })
        neutral = simulate([{k: v for k, v in r.items() if k != "features"} for r in baseline_events])
        if neutral["accepted_n"] != reference["accepted_n"] or abs(neutral["realized_pnl"] - reference["realized_pnl"]) > .011:
            raise ValueError("REFERENCE_RECONCILIATION_FAILED")
        neutral_quarters = entry_quarter_attribution(neutral)
        scenarios = {}
        for name, (feature, direction) in PRIORITIES.items():
            if any(not isinstance(r["features"].get(feature), (int, float))
                   or isinstance(r["features"].get(feature), bool)
                   or not math.isfinite(r["features"][feature]) for r in baseline_events):
                scenarios[name] = {"status": "BLOCKED_MISSING_PREENTRY_FEATURE",
                                   "feature": feature, "trade_ready": False}
                continue
            signals = [{k: v for k, v in row.items() if k != "features"} |
                       {"score": direction * row["features"][feature]} for row in baseline_events]
            sim = simulate(signals, priority_mode="score_desc")
            neutral_keys = {(r["symbol"], r["entry_day"]) for r in neutral["accepted_signals"]}
            selected_keys = {(r["symbol"], r["entry_day"]) for r in sim["accepted_signals"]}
            overlap = neutral_keys & selected_keys
            scenarios[name] = {
                "selection_difference_attribution": selection_difference_attribution(neutral, sim),
                "volume_leave_one_symbol_out": volume_leave_one_symbol_out(baseline_events) if name == "volume_high_first" else None,
                "accepted_trade_overlap_vs_neutral": {
                    "shared_n": len(overlap),
                    "only_neutral_n": len(neutral_keys - selected_keys),
                    "only_priority_n": len(selected_keys - neutral_keys),
                    "jaccard_similarity": round(len(overlap) / len(neutral_keys | selected_keys), 4)
                    if neutral_keys | selected_keys else None,
                },
                "status": "EXPLORATORY_ONLY",
                "accepted_n": sim["accepted_n"],
                "rejected_n": sim["rejected_n"],
                "realized_pnl": sim["realized_pnl"],
                "realized_return_pct": sim["realized_return_pct"],
                "pnl_difference_vs_symbol_asc": round(sim["realized_pnl"] - neutral["realized_pnl"], 2),
                "capital_occupancy": calendar_capital_occupancy(sim),
                "entry_quarter_attribution": entry_quarter_attribution(sim),
                "entry_quarter_pnl_difference_vs_neutral": {
                    q: round(entry_quarter_attribution(sim).get(q, {}).get("entry_attributed_pnl", 0) -
                             neutral_quarters.get(q, {}).get("entry_attributed_pnl", 0), 2)
                    for q in sorted(set(neutral_quarters) | set(entry_quarter_attribution(sim)))},
                "trade_ready": False,
            }
        results[cohort] = {
            "neutral_symbol_asc": {"accepted_n": neutral["accepted_n"],
                                   "realized_pnl": neutral["realized_pnl"],
                                   "entry_quarter_attribution": neutral_quarters},
            "scenarios": scenarios,
            "predeclared_directions_not_tuned_on_outcomes": True,
            "independent_validation": False,
            "trade_ready": False
        }
    return {"status": "EXPLORATORY_ONLY", "trade_ready": False, "cohorts": results,
            "limitations": ["Previously inspected held-out sample, not independent confirmation",
                            "Single-feature ranking; no walk-forward recalibration",
                            "Fixed exits, no daily marked-to-market risk or live execution",
                            "Feature missingness blocks scenario; never silently imputes",
                            "No strategy chosen by historical maximum",
                            "Entry-quarter PnL attribution is not a standalone quarterly portfolio backtest"]}


def main():
    import json
    from pathlib import Path
    source = json.loads(Path("reports/candidate_feature_oos.json").read_text(encoding="utf-8"))
    result = {pattern: priority_experiment(portfolio)
              for pattern, portfolio in source["portfolio_oos"].items()}
    dest = Path("reports/candidate_preentry_priority_experiment.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"status": "EXPLORATORY_ONLY", "patterns": sorted(result)}))


if __name__ == "__main__":
    main()
