"""Predeclared ex-ante priority sensitivity on an EXISTING OOS candidate audit.

No fitted weights, no future-return scoring, no live signal changes. Research only.
"""
import math
from candidate_portfolio_capacity import simulate, calendar_capital_occupancy

DIRECTIONS = {"relative_strength_20d_pct": 1,
              "volume_ratio_20d": 1,
              "atr_14_pct": -1}


def score_from_signal_close(features, thresholds):
    if not isinstance(features, dict) or features.get("status") != "DESCRIPTIVE_ONLY":
        raise ValueError("UNVERIFIED_SIGNAL_CLOSE_FEATURES")
    if not isinstance(thresholds, dict) or set(DIRECTIONS) - set(thresholds):
        raise ValueError("MISSING_TRAINING_THRESHOLDS")
    components = []
    for key, direction in DIRECTIONS.items():
        value, threshold = features.get(key), thresholds[key]
        if any(not isinstance(x, (float, int)) or isinstance(x, bool) or not math.isfinite(x)
               for x in (value, threshold)):
            raise ValueError("INVALID_PREENTRY_FEATURE")
        # Scale relative to threshold without tuning on held-out returns.
        scale = max(abs(threshold), 1.0)
        components.append(max(-2.0, min(2.0, direction * (value - threshold) / scale)))
    return round(sum(components), 10)


def compare_priorities(candidate_audit, *, pattern=None):
    if not isinstance(candidate_audit, list):
        raise ValueError("INVALID_CANDIDATE_AUDIT")
    events = []
    seen = set()
    for row in candidate_audit:
        if not isinstance(row, dict):
            raise ValueError("INVALID_CANDIDATE_AUDIT_ROW")
        key = (row.get("symbol"), row.get("entry_day"))
        if key in seen:
            raise ValueError("DUPLICATE_CANDIDATE")
        seen.add(key)
        outcome = row.get("historical_net_return_pct_outcome_not_selection_input")
        if not isinstance(outcome, (float, int)) or isinstance(outcome, bool) or not math.isfinite(outcome):
            raise ValueError("INVALID_OUTCOME_FOR_PORTFOLIO_ACCOUNTING")
        score = score_from_signal_close(row.get("features_at_signal_close"),
                                        row.get("training_thresholds"))
        events.append({"symbol": row["symbol"], "entry_day": row["entry_day"],
                       "exit_day": row["exit_day"], "net_return_pct": outcome,
                       "score": score})
    scenarios = {mode: simulate(events, priority_mode=mode)
                 for mode in ("symbol_asc", "symbol_desc", "stable_hash", "score_desc")}
    return {"status": "RESEARCH_ONLY_EX_ANTE_PRIORITY_SENSITIVITY",
            "pattern": pattern, "event_count": len(events),
            "score_inputs": list(DIRECTIONS), "weights_fitted_on_outcomes": False,
            "future_outcomes_used_for_priority": False,
            "priority": {mode: {
                "accepted_n": p["accepted_n"], "rejected_n": p["rejected_n"],
                "realized_pnl": p["realized_pnl"],
                "capital_occupancy": calendar_capital_occupancy(p)}
                for mode, p in scenarios.items()},
            "trade_ready": False, "independent_oos_validation": False,
            "limitation": "Research feature score, not a proven predictive rank; source audit must be frozen and checked."}
