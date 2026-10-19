"""Silent geopolitical market-risk assessment, never a standalone sell/buy signal."""
from datetime import datetime, timezone

RISK_TERMS = ("war", "invasion", "missile", "military strike", "armed conflict",
              "escalation", "retaliation", "sanctions", "oil supply disruption",
              "shipping disruption", "ceasefire collapse", "attack")

def evaluate_risk(context, quotes, now=None):
    now = now or datetime.now(timezone.utc)
    headlines = context.get("headlines", [])
    risk_headlines = [h for h in headlines if any(
        word in h.get("headline", "").lower() for word in RISK_TERMS)]
    result = {"status": "UNVERIFIED", "risk_headline_count": len(risk_headlines),
              "broad_selloff": False, "volatility_proxy_rising": False,
              "sector_divergence": False, "notify": False, "trade_ready": False}
    if not risk_headlines or context.get("status") != "HEADLINE_REVIEW_ONLY":
        result["status"] = "NO_VERIFIED_RISK_CONTEXT"
        return result
    def change(symbol):
        item = quotes.get(symbol, {})
        try:
            ts = datetime.fromisoformat(item["timestamp_utc"].replace("Z", "+00:00"))
            age = (now - ts).total_seconds()
            value = float(item["change_pct"])
            if ts.tzinfo is None or not -30 <= age <= 900 or not -20 <= value <= 20:
                return None
            return value
        except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
            return None
    spy, qqq, vixy, xle, ita = (change(t) for t in ("SPY", "QQQ", "VIXY", "XLE", "ITA"))
    if spy is None or qqq is None:
        result["status"] = "INDEX_DATA_MISSING"
        return result
    result["broad_selloff"] = spy < -0.5 and qqq < -0.5
    result["volatility_proxy_rising"] = vixy is not None and vixy > 1
    result["sector_divergence"] = any(v is not None and v > spy + 1 for v in (xle, ita))
    result["status"] = ("RISK_OFF_RESEARCH" if result["broad_selloff"] else "RISK_HEADLINE_MARKET_NOT_CONFIRMED")
    return result
