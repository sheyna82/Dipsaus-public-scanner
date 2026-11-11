"""Compare an identical set of dated opportunities with/without a regime gate.

No position overlap model or independently authenticated price data. Fixed
candidate returns are research proxies. Skipped trades earn zero, not the
benchmark return; this explicitly measures cash drag.
"""
from math import isfinite
from statistics import mean
from research_swing_short_regime_gate import assess_short_swing_regime

def compare_regime_gating(opportunities):
    if not isinstance(opportunities, (list, tuple)) or not opportunities:
        raise ValueError("empty_opportunities")
    seen = set()
    rows = []
    for opportunity in opportunities:
        if not isinstance(opportunity, dict):
            raise ValueError("invalid_opportunity")
        key = (opportunity.get("decision_date"), opportunity.get("symbol"),
               opportunity.get("horizon"))
        if any(x is None for x in key) or key in seen:
            raise ValueError("duplicate_or_missing_opportunity_key")
        seen.add(key)
        horizon = opportunity["horizon"]
        if type(horizon) is not int or horizon not in (5, 10, 15):
            raise ValueError("invalid_horizon")
        net = opportunity.get("net_return_pct")
        if isinstance(net, bool) or not isinstance(net, (float, int)) or not isfinite(net):
            raise ValueError("invalid_net_return")
        regime = assess_short_swing_regime(opportunity.get("index_closes"))
        accepted = regime["new_entries_permitted_for_research"]
        rows.append({"decision_date": key[0], "symbol": key[1], "horizon": horizon,
                     "regime": regime["state"], "accepted": accepted,
                     "ungated_net_pct": net, "gated_cash_adjusted_pct": net if accepted else 0.0})
    return {"research_only": True, "trade_ready": False, "independent_edge_proven": False,
            "opportunities": len(rows), "accepted": sum(r["accepted"] for r in rows),
            "skipped": sum(not r["accepted"] for r in rows),
            "mean_ungated_net_pct": mean(r["ungated_net_pct"] for r in rows),
            "mean_gated_cash_adjusted_pct": mean(r["gated_cash_adjusted_pct"] for r in rows),
            "rows": rows,
            "limitations": ["equal notional opportunities", "no overlapping portfolio capital accounting",
                            "no independent market-data authentication"]}
