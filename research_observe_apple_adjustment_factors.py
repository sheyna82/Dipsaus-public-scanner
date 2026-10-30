"""Observe adjusted-close factor changes in the real public Apple sample."""
import json
from research_audit_aapl_spy_adjustments import read_public_csv, APPLE_URL
from dipsaus_offline_adjustment_factor_audit import audit_adjusted_close_factors


def audit_real_apple_factors():
    rows = read_public_csv(APPLE_URL)
    if len(rows) != 506:
        raise ValueError("unexpected_apple_history")
    result = audit_adjusted_close_factors([
        {"close": r["AAPL.Close"], "adjusted": r["AAPL.Adjusted"]}
        for r in rows
    ])
    if result["status"] != "RESEARCH_ONLY":
        raise ValueError("invalid_adjustment_factors")
    return {
        "source": APPLE_URL,
        "first_date": rows[0]["Date"],
        "last_date": rows[-1]["Date"],
        "rows": result["rows"],
        "factor_min": result["factor_min"],
        "factor_max": result["factor_max"],
        "factor_change_events_gt_0_1pct": result["factor_change_events_gt_0_1pct"],
        "factor_change_dates": [rows[i]["Date"] for i in result["factor_change_indices"]],
        "policy_verified": False,
        "trade_ready": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit_real_apple_factors(), indent=2, sort_keys=True))
