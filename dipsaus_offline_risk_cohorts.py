"""Offline matched-cohort comparison for risk warnings; no trading or alerts.

Caller supplies separately evaluated warning and no-warning observations.
No claim of causal effect: matching, sampling and provenance need independent audit.
"""
import math


def compare_risk_cohorts(warnings, controls, horizon=5, min_per_group=5):
    if (type(horizon) is not int or horizon < 1 or type(min_per_group) is not int
            or min_per_group < 1 or not isinstance(warnings, (list, tuple))
            or not isinstance(controls, (list, tuple))):
        return None

    def extract(items):
        usable, missing, review, invalid = [], 0, 0, 0
        for item in items:
            if not isinstance(item, dict) or item.get("research_only") is not True or item.get("trade_ready") is not False:
                invalid += 1
                continue
            if item.get("source_attested_not_verified") is not True:
                invalid += 1
                continue
            horizons = item.get("horizons")
            if not isinstance(horizons, dict) or horizon not in horizons or horizons[horizon] is None:
                missing += 1
                continue
            point = horizons[horizon]
            if not isinstance(point, dict):
                invalid += 1
                continue
            if point.get("large_gap_manual_review") is not False:
                review += 1
                continue
            decline = point.get("worst_future_low_pct")
            if type(decline) not in (int, float) or not math.isfinite(decline):
                invalid += 1
                continue
            usable.append(float(decline))
        return {"nominated": len(items), "evaluated": len(usable),
                "missing": missing, "manual_review": review, "invalid": invalid,
                "mean_worst_future_low_pct": round(sum(usable) / len(usable), 4) if usable else None}, usable

    w, wvals = extract(warnings)
    c, cvals = extract(controls)
    sufficient = len(wvals) >= min_per_group and len(cvals) >= min_per_group
    difference = (round(w["mean_worst_future_low_pct"] - c["mean_worst_future_low_pct"], 4)
                  if sufficient else None)
    return {"warning_group": w, "no_warning_group": c, "horizon_sessions": horizon,
            "minimum_sample_met": sufficient, "difference_percentage_points": difference,
            "research_only": True, "trade_ready": False, "order_instruction": None,
            "limitations": "Not matched automatically; no causal inference, verified data or live performance."}
