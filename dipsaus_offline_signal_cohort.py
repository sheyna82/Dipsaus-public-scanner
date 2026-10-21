"""Offline cohort summary for historical signal studies.

Do not treat this as evidence of a profitable strategy: selection bias,
survivorship bias, corporate actions and execution assumptions remain open.
"""
import math


def summarize_outcomes(outcomes, horizon):
    """Summarize all nominated signals, retaining missing and review counts."""
    if not isinstance(outcomes, (list, tuple)) or not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        return None
    total = len(outcomes)
    valid = []
    missing = review = invalid = 0
    for item in outcomes:
        if not isinstance(item, dict) or item.get("research_only") is not True or item.get("trade_ready") is not False:
            invalid += 1
            continue
        data = item.get("horizons")
        if not isinstance(data, dict) or horizon not in data or data[horizon] is None:
            missing += 1
            continue
        point = data[horizon]
        if not isinstance(point, dict):
            invalid += 1
            continue
        value = point.get("estimated_net_close_return_pct")
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            invalid += 1
            continue
        if point.get("manual_review_required") is not False or item.get("data_provenance_independently_verified") is not False:
            review += 1
            continue
        valid.append(float(value))
    # Explicitly count every candidate; never hide non-evaluable observations.
    return {
        "horizon_sessions": horizon,
        "nominated": total,
        "evaluated": len(valid),
        "missing": missing,
        "manual_review": review,
        "invalid": invalid,
        "coverage_pct": round(100 * len(valid) / total, 2) if total else None,
        "mean_estimated_net_return_pct": round(sum(valid) / len(valid), 4) if valid else None,
        "positive_share_pct": round(100 * sum(v > 0 for v in valid) / len(valid), 2) if valid else None,
        "research_only": True,
        "trade_ready": False,
    }
