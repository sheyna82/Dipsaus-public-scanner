"""Conservative market confirmation for silent macro research, not a trading gate."""
from datetime import datetime, timezone

def assess_macro_market(context, quotes, now=None):
    """Require fresh broad-index confirmation; never infer trade readiness from headlines."""
    now = now or datetime.now(timezone.utc)
    result = {"status": "INSUFFICIENT_MARKET_CONFIRMATION", "direction": "UNVERIFIED",
              "macro_context_present": bool(context.get("headlines")),
              "trade_ready": False, "notify": False, "index_checks": {}}
    if context.get("status") != "HEADLINE_REVIEW_ONLY" or not context.get("headlines"):
        return result
    for ticker in ("SPY", "QQQ"):
        quote = quotes.get(ticker, {})
        try:
            timestamp = datetime.fromisoformat(quote["timestamp_utc"].replace("Z", "+00:00"))
            age = (now - timestamp).total_seconds()
            change = float(quote["change_pct"])
            valid = timestamp.tzinfo is not None and -30 <= age <= 900 and -20 <= change <= 20
        except (KeyError, TypeError, ValueError, OverflowError):
            valid = False
            change = None
        result["index_checks"][ticker] = {"fresh": valid, "positive": bool(valid and change > 0.25)}
    checks = result["index_checks"]
    if all(checks[t]["fresh"] for t in ("SPY", "QQQ")):
        if all(checks[t]["positive"] for t in ("SPY", "QQQ")):
            result["status"] = "BROAD_MARKET_POSITIVE_RESEARCH"
            result["direction"] = "POSITIVE"
        else:
            result["status"] = "BROAD_MARKET_NOT_CONFIRMED"
    return result
