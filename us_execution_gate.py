"""Fail-closed execution gate. Explicit independently verified inputs only; no broker API."""
import math
from datetime import datetime, timezone

REQUIRED = ("symbol","quote_utc","ask_usd","bid_usd","eur_per_usd","fx_utc",
            "invalidation_usd","first_meaningful_resistance_usd","realistic_target_usd",
            "bottom_confirmed","daily_weekly_reviewed","resistance_confirmed",
            "company_event_risk_verified","recent_price_moving_news_verified",
            "upcoming_material_events_verified","corporate_actions_verified",
            "portfolio_fit_verified","broker_quote_verified","fx_verified")

def evaluate_trade(evidence, now=None, budget_eur=3500, max_risk_eur=None):
    """Return a non-executable, human-reviewed calculation; never place an order."""
    now = now or datetime.now(timezone.utc)
    missing = [k for k in REQUIRED if k not in evidence or evidence[k] is None]
    if missing:
        return {"status":"DATA_BLOCKED","missing":missing,"trade_ready":False}
    flags = [k for k in REQUIRED if k.endswith("_verified") or k in
             ("bottom_confirmed","daily_weekly_reviewed","resistance_confirmed")]
    unverified = [k for k in flags if evidence[k] is not True]
    if unverified:
        return {"status":"REVIEW_BLOCKED","unverified":unverified,"trade_ready":False}
    try:
        quote = datetime.fromisoformat(evidence["quote_utc"].replace("Z","+00:00"))
        fx_time = datetime.fromisoformat(evidence["fx_utc"].replace("Z","+00:00"))
        if quote.utcoffset() is None or fx_time.utcoffset() is None:
            raise ValueError("timezone required")
        ages = [(now - t.astimezone(timezone.utc)).total_seconds() for t in (quote,fx_time)]
        if any(a < -60 or a > 300 for a in ages):
            return {"status":"STALE_OR_FUTURE_DATA","ages_seconds":ages,"trade_ready":False}
        ask,bid,fx,stop,friction,target = (float(evidence[k]) for k in
            ("ask_usd","bid_usd","eur_per_usd","invalidation_usd",
             "first_meaningful_resistance_usd","realistic_target_usd"))
        if not all(math.isfinite(x) and x>0 for x in (ask,bid,fx,stop,friction,target)):
            raise ValueError("nonpositive or nonfinite")
        if not (stop < bid <= ask < friction <= target):
            return {"status":"STRUCTURE_BLOCKED","trade_ready":False}
        if not (math.isfinite(budget_eur) and budget_eur>0):
            raise ValueError("invalid budget")
        shares = math.floor(budget_eur/(ask*fx))
        if shares<1:
            return {"status":"BUDGET_BLOCKED","trade_ready":False}
        cost = shares*ask*fx
        risk = shares*(ask-stop)*fx
        gross_first = shares*(friction-ask)*fx
        gross_target = shares*(target-ask)*fx
        rr_first = (friction-ask)/(ask-stop)
        rr_target = (target-ask)/(ask-stop)
        risk_cap = max_risk_eur
        if risk_cap is not None and (not math.isfinite(risk_cap) or risk_cap<=0):
            raise ValueError("invalid risk cap")
        checks = {"target_gross_at_least_150_eur":gross_target>=150,
                  "target_rr_at_least_2":rr_target>=2,
                  "risk_within_cap":risk_cap is not None and risk<=risk_cap,
                  "first_resistance_reviewed":True}
        return {"status":"HUMAN_REVIEW_REQUIRED" if all(checks.values()) else "MONEY_OR_RISK_BLOCKED",
                "trade_ready":False,"order_placement_enabled":False,
                "symbol":evidence["symbol"],"whole_shares":shares,
                "budget_eur":budget_eur,"notional_eur":round(cost,2),
                "risk_eur":round(risk,2),"first_resistance_gross_eur":round(gross_first,2),
                "target_gross_eur":round(gross_target,2),
                "first_resistance_rr":round(rr_first,2),"target_rr":round(rr_target,2),
                "checks":checks,
                "limitations":"Manual independent evidence required, including recent price-moving company news and upcoming material events (earnings, tenders/bids, court/regulatory decisions, investor days, financing/capital actions and other known catalysts). Ignores fees, taxes, slippage, order-book depth and EUR FX spread. Target beyond first resistance is conditional; no auto-trading or verified executable setup."}
    except (ValueError,TypeError,OverflowError) as exc:
        return {"status":"INVALID_EVIDENCE","error":str(exc),"trade_ready":False}

