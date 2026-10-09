"""Daily/weekly historical recovery research; NEVER an executable trading signal."""
from datetime import date
from statistics import median

def _p(x):
    return round(float(x), 4)

def _weekly(rows):
    weeks = {}
    for row in rows:
        d = date.fromisoformat(row["date"])
        key = d.isocalendar()[:2]
        if key not in weeks:
            weeks[key] = dict(row)
        else:
            w = weeks[key]
            w["high"] = max(w["high"], row["high"])
            w["low"] = min(w["low"], row["low"])
            w["close"] = row["close"]
            w["volume"] += row["volume"]
            w["date"] = row["date"]
    return list(weeks.values())

def _pivots(rows, span=2):
    result = []
    for i in range(span, len(rows)-span):
        h = rows[i]["high"]
        if h > max(x["high"] for x in rows[i-span:i]) and h >= max(x["high"] for x in rows[i+1:i+span+1]):
            result.append({"date": rows[i]["date"], "high_usd": _p(h)})
    return result

def _zones(pivots, close, tolerance=0.015):
    groups = []
    for p in sorted((p for p in pivots if p["high_usd"] > close), key=lambda p:p["high_usd"]):
        if groups and abs(p["high_usd"] / median(x["high_usd"] for x in groups[-1]) - 1) <= tolerance:
            groups[-1].append(p)
        else:
            groups.append([p])
    return [{"low_usd":_p(min(x["high_usd"] for x in group)),
             "high_usd":_p(max(x["high_usd"] for x in group)),
             "touches":len(group), "dates":[x["date"] for x in group],
             "status":"HISTORICAL_PIVOT_CLUSTER_UNCONFIRMED"}
            for group in groups]

def recovery_map(rows, six_month_high=None):
    if len(rows) < 65:
        return {"status":"INSUFFICIENT_HISTORY", "trade_ready":False}
    r = rows[-65:]
    last = r[-1]
    close = float(last["close"])
    lows = [x["low"] for x in r]
    highs = [x["high"] for x in r]
    closes = [x["close"] for x in r]
    volumes = [x["volume"] for x in r]
    bottom = min(lows)
    bottom_idx = lows.index(bottom)
    prior_low = min(lows[-40:-20])
    recent_low = min(lows[-20:])
    prior_20_high = max(highs[-41:-21])
    avg_volume = sum(volumes[-21:-1])/20
    signals = {
        "higher_20d_low":recent_low > prior_low,
        "above_20d_close_mean":close > sum(closes[-20:])/20,
        "positive_5d_close":close > closes[-6],
        "above_previous_20d_high":close > prior_20_high,
        "volume_above_previous_20d_mean":volumes[-1] > avg_volume,
    }
    weeks = _weekly(rows)
    # Last calendar week may be incomplete: report separately, never claim confirmed weekly close.
    completed = weeks[:-1]
    weekly = {
        "completed_week_count":len(completed),
        "latest_week_incomplete":True,
        "last_completed_week_end":completed[-1]["date"] if completed else None,
        "last_completed_week_close_usd":_p(completed[-1]["close"]) if completed else None,
        "prior_completed_week_close_usd":_p(completed[-2]["close"]) if len(completed)>1 else None,
        "completed_week_close_rising":completed[-1]["close"]>completed[-2]["close"] if len(completed)>1 else None,
        "completed_week_higher_low":completed[-1]["low"]>completed[-2]["low"] if len(completed)>1 else None,
        "historical_weekly_structure_only":True,
    }
    pivots = _pivots(rows)
    zones = _zones(pivots, close)
    invalidation = min(lows[-10:])
    risk_per_share = close - invalidation
    # Illustrative arithmetic only, not validated risk or targets.
    hypothetical = []
    for z in zones:
        reward = z["low_usd"] - close
        hypothetical.append({
            "zone_low_usd":z["low_usd"],
            "gross_usd_on_3500_usd_notional":round(3500*reward/close,2),
            "reference_rr":round(reward/risk_per_share,2) if risk_per_share>0 else None,
            "passes_150_usd_reference":3500*reward/close>=150,
            "passes_2r_reference":risk_per_share>0 and reward/risk_per_share>=2,
        })
    return {
        "status":"STRUCTURED_HISTORICAL_RESEARCH_ONLY",
        "last_bar_date":last["date"],
        "daily_structure":{
            "last_close_usd":_p(close),
            "observed_65d_low_usd":_p(bottom),
            "bottom_bar_date":r[bottom_idx]["date"],
            "recent_20d_low_usd":_p(recent_low),
            "prior_20d_low_usd":_p(prior_low),
            "observed_65d_high_usd":_p(max(highs)),
            "rebound_from_65d_low_pct":round((close/bottom-1)*100,2),
        },
        "weekly_structure":weekly,
        "bottom_evidence":signals,
        "bottom_signal_count":sum(signals.values()),
        "bottom_confirmed":False,
        "first_friction_reference_usd":_p(min((h for h in highs[-20:-1] if h>close),default=0)) or None,
        "historical_overhead_pivot_zones":zones,
        "observed_six_month_high_usd":_p(six_month_high) if six_month_high else None,
        "recent_10d_low_invalidation_reference_usd":_p(invalidation),
        "invalidation_confirmed":False,
        "hypothetical_reference_math_usd":hypothetical,
        "euro_money_gate_verified":False,
        "company_event_risk_verified":False,
        "corporate_actions_verified":False,
        "resistance_confirmed":False,
        "recovery_zone_confirmed":False,
        "rr_verified":False,
        "broker_quote_verified":False,
        "portfolio_fit_verified":False,
        "trade_ready":False,
        "limitations":"Daily bars aggregated into completed historical weeks; no independent weekly feed. Pivot clusters and 10d low are NOT validated resistance/invalidations. $3500 fractional-share math is NOT EUR 3500 sizing: excludes FX, whole shares, spread, fees, slippage and event risk. No DEGIRO executable quote, corporate-action adjustment validation or company/event/portfolio assessment."
    }

