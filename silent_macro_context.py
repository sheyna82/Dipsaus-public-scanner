"""Silent macro-catalyst research. Never creates a trade signal or phone notification."""
import json
import os
import re
import urllib.request
from datetime import datetime, timezone, timedelta

TERMS = {
    "trade_policy": ("tariff", "trade deal", "import duty", "trade restriction"),
    "monetary_policy": ("federal reserve", "fed rate", "interest rate", "powell"),
    "geopolitics": ("sanction", "export control", "ceasefire", "war", "invasion", "missile", "military strike", "armed conflict", "escalation", "retaliation", "oil supply disruption", "shipping disruption", "attack"),
    "fiscal_policy": ("white house", "executive order", "treasury"),
}

def classify(items):
    """Headline triage only: not source verification, direction or trading advice."""
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = item.get("headline")
        if not isinstance(title, str):
            continue
        matches = [name for name, words in TERMS.items()
                   if any(re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", title.lower()) for word in words)]
        if matches:
            result.append({"categories": matches, "headline": title[:200],
                           "source": str(item.get("source", ""))[:70],
                           "published": item.get("datetime") if isinstance(item.get("datetime"), int) else None})
    return result[:12]

def update_silent_context(state, now=None, fetch=None):
    """Private hourly cache; fail closed. Never sends notifications."""
    now = now or datetime.now(timezone.utc)
    previous = state.get("silent_macro_context", {})
    try:
        last = datetime.fromisoformat(previous.get("checked_utc", ""))
        if last.tzinfo and timedelta(0) <= now - last < timedelta(hours=1):
            return previous
    except (ValueError, TypeError):
        pass
    context = {"checked_utc": now.isoformat(), "status": "UNAVAILABLE",
               "headlines": [], "trade_ready": False, "notify": False,
               "note": "Research context only; no verified policy, market reaction or entry confirmation"}
    token = os.environ.get("FINNHUB_API_KEY")
    if not token and fetch is None:
        context["status"] = "NO_PROVIDER_KEY"
    else:
        try:
            if fetch is None:
                request = urllib.request.Request("https://finnhub.io/api/v1/news?category=general",
                    headers={"X-Finnhub-Token": token, "User-Agent": "DIPSAUS silent research"})
                with urllib.request.urlopen(request, timeout=8) as response:
                    items = json.load(response)
            else:
                items = fetch()
            if not isinstance(items, list):
                raise ValueError("INVALID_FEED")
            context["headlines"] = classify(items)
            context["status"] = "HEADLINE_REVIEW_ONLY"
        except Exception:
            context["status"] = "PROVIDER_UNAVAILABLE"
    # Use only independently supplied, timestamped market data. No stale quote inference. 
    from macro_market_confirmation import assess_macro_market 
    from macro_index_quotes import fetch_index_quotes
    quotes = fetch_index_quotes() if context["status"] == "HEADLINE_REVIEW_ONLY" and context["headlines"] else {} 
    context["market_confirmation"] = assess_macro_market(context, quotes, now)
    from macro_risk_watch import evaluate_risk
    context["market_risk"] = evaluate_risk(context, quotes, now) 
    state["silent_macro_context"] = context 
    return context
