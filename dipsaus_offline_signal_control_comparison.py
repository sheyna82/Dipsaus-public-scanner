"""Research-only matched no-signal comparison and intratrade downside.

Inputs are local historical rows; never reads portfolio state or places orders.
"""
from math import sqrt


def compare_signal_controls(rows, *, min_group=5):
    """Compare chronological evaluation rows with scores, returns and optional lows.

    Both groups must come from the same ticker, period and sampling schedule.
    This is descriptive, not a causal or predictive estimate.
    """
    if not isinstance(rows, list) or type(min_group) is not int or min_group < 2:
        return {"status": "REJECTED", "reason": "invalid_input"}
    if any(not isinstance(r, dict) or type(r.get("score")) not in (int, float)
           or type(r.get("net_return_pct")) not in (int, float)
           for r in rows):
        return {"status": "REJECTED", "reason": "invalid_rows"}
    selected = [r for r in rows if r["score"] >= 5]
    controls = [r for r in rows if r["score"] < 5]
    if min(len(selected), len(controls)) < min_group:
        return {"status": "INSUFFICIENT_SAMPLE",
                "selected_count": len(selected), "control_count": len(controls),
                "trade_ready": False}
    def stats(group):
        values = [r["net_return_pct"] for r in group]
        mean = sum(values) / len(values)
        downside = [r["max_adverse_excursion_pct"] for r in group
                    if type(r.get("max_adverse_excursion_pct")) in (int, float)]
        return {"count": len(values), "mean_net_pct": mean,
                "win_rate": sum(x > 0 for x in values) / len(values),
                "sample_sd_pct": sqrt(sum((x - mean) ** 2 for x in values) /
                                      (len(values) - 1)),
                "mean_mae_pct": sum(downside) / len(downside) if downside else None,
                "mae_coverage": len(downside)}
    a, b = stats(selected), stats(controls)
    return {"status": "EXPLORATORY_ONLY", "selected": a, "no_signal": b,
            "mean_difference_pct_points": a["mean_net_pct"] - b["mean_net_pct"],
            "trade_ready": False,
            "limitations": "Unmatched score groups; possible regime and volatility confounding, selection bias, serial dependence and incomplete downside coverage. Use longer out-of-sample periods."}
