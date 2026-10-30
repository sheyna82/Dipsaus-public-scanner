"""Deterministic offline matching of warning and no-warning research observations.

Matching is exact on market regime and sector, with a configurable ATR%
caliper. Caller-supplied labels are not independently verified. Each control
is used at most once. No outcomes are read during matching.
"""
import math
from datetime import date


def match_risk_controls(warnings, controls, max_atr_pct_gap=1.0, max_calendar_days=7):
    if (not isinstance(warnings, (list, tuple))
            or not isinstance(controls, (list, tuple))
            or type(max_atr_pct_gap) not in (int, float)
            or not math.isfinite(max_atr_pct_gap) or max_atr_pct_gap < 0
            or type(max_calendar_days) is not int or max_calendar_days < 0):
        return None

    def _valid_date(value):
        try:
            return date.fromisoformat(value).isoformat() == value
        except ValueError:
            return False

    def valid(item):
        return (isinstance(item, dict)
                and type(item.get("id")) is str and bool(item["id"])
                and type(item.get("market_regime")) is str and bool(item["market_regime"])
                and type(item.get("sector")) is str and bool(item["sector"])
                and type(item.get("signal_date")) is str
                and _valid_date(item["signal_date"])
                and type(item.get("atr_pct")) in (int, float)
                and math.isfinite(item["atr_pct"]) and item["atr_pct"] >= 0)
    if any(not valid(x) for x in [*warnings, *controls]):
        return None
    ids = [x["id"] for x in [*warnings, *controls]]
    if len(ids) != len(set(ids)):
        return None
    used = set()
    pairs, unmatched = [], []
    for warning in warnings:
        candidates = [(abs(warning["atr_pct"] - control["atr_pct"]), control["id"], control)
                      for control in controls
                      if control["id"] not in used
                      and warning["market_regime"] == control["market_regime"]
                      and warning["sector"] == control["sector"]
                      and abs((date.fromisoformat(warning["signal_date"]) -
                               date.fromisoformat(control["signal_date"])).days) <= max_calendar_days
                      and abs(warning["atr_pct"] - control["atr_pct"]) <= max_atr_pct_gap]
        if not candidates:
            unmatched.append(warning["id"])
            continue
        _, _, selected = min(candidates, key=lambda item: (item[0], item[1]))
        used.add(selected["id"])
        pairs.append({"warning_id": warning["id"], "control_id": selected["id"],
                      "calendar_day_gap": abs((date.fromisoformat(warning["signal_date"]) -
                                               date.fromisoformat(selected["signal_date"])).days),
                      "atr_pct_gap": round(abs(warning["atr_pct"] - selected["atr_pct"]), 4)})
    return {"pairs": pairs, "unmatched_warning_ids": unmatched,
            "nominated_warnings": len(warnings), "matched_warnings": len(pairs),
            "matched_share_pct": round(100 * len(pairs) / len(warnings), 2) if warnings else None,
            "research_only": True, "trade_ready": False, "order_instruction": None,
            "limitations": "Greedy matching; dates and regime/sector labels caller supplied; no causal proof."}
