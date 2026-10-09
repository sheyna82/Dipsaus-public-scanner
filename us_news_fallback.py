"""Optional Finnhub news/earnings research when SEC is blocked. Never clears event risk."""
import json
import os
import urllib.parse
import urllib.request
from datetime import date, timedelta, datetime, timezone

KEYWORDS = ("strategic review", "special committee", "strategic alternatives", "going concern", "reverse stock split", "reverse split", "share consolidation", "trading halt", "halted", "nasdaq compliance", "noncompliance", "non-compliance", "liquidity", "asset sale", "tender offer", "takeover", "buyout", "financing", "capital raise", "private placement", "at-the-market", "atm offering", "shareholder vote", "earnings", "results", "guidance", "offering", "dilution", "split", "merger",
            "acquisition", "bankruptcy", "lawsuit", "investigation", "delisting", "fda",
            "recall", "restatement", "dividend", "debt", "restructur", "sec filing")

def _fetch(path, params, token):
    url = "https://finnhub.io/api/v1/" + path + "?" + urllib.parse.urlencode(params)
    request = urllib.request.Request(url, headers={"X-Finnhub-Token": token,
        "User-Agent": "Dipsaus research-only scanner"})
    with urllib.request.urlopen(request, timeout=15) as response:
        return json.load(response)

def fallback_news(symbol, today=None, token=None):
    token = token or os.environ.get("FINNHUB_API_KEY")
    result = {"source":"Finnhub company-news + earnings-calendar",
              "status":"UNAVAILABLE", "news_status":"NOT_CHECKED",
              "earnings_status":"NOT_CHECKED", "headline_review":[],"flagged_headline_review":[],"headline_count_total":0,"flagged_count_total":0,
              "earnings_dates":[], "company_event_risk_verified":False,
              "corporate_actions_verified":False, "reason":None}
    if not token:
        result["reason"] = "FINNHUB_API_KEY not configured"
        return result
    today = today or date.today()
    start = today - timedelta(days=14)
    end = today + timedelta(days=30)
    try:
        news = _fetch("company-news", {"symbol":symbol,"from":start.isoformat(),
                                     "to":today.isoformat()}, token)
        if not isinstance(news, list):
            raise ValueError("NEWS_NOT_LIST")
        result["news_status"] = "FETCHED" if news else "EMPTY_UNVERIFIED"
        for item in news:
            if not isinstance(item,dict):
                continue
            headline = item.get("headline","")
            if not isinstance(headline,str) or not headline.strip():
                continue
            published = item.get("datetime")
            if not isinstance(published,(int,float)):
                continue
            link = item.get("url")
            if not isinstance(link,str) or not link.startswith("https://"):
                link = None
            result["headline_review"].append({
                "headline":headline[:250],"source":str(item.get("source",""))[:90],
                "published_utc":datetime.fromtimestamp(published,timezone.utc).isoformat(),
                "url":link,"keyword_flag":any(k in headline.lower() for k in KEYWORDS),
                "review_reason":"MATERIAL_EVENT_KEYWORD" if any(k in headline.lower() for k in KEYWORDS) else "GENERAL_NEWS"})
        result["headline_review"].sort(key=lambda x:x["published_utc"],reverse=True)
        result["headline_count_total"] = len(result["headline_review"])
        flagged = [x for x in result["headline_review"] if x["keyword_flag"]]
        result["flagged_count_total"] = len(flagged)
        result["flagged_headline_review"] = flagged[:20]
        result["headline_review"] = result["headline_review"][:20]
    except Exception as exc:
        result["news_status"] = "FAILED: "+type(exc).__name__
    try:
        calendar = _fetch("calendar/earnings",{"symbol":symbol,"from":today.isoformat(),
                                               "to":end.isoformat()},token)
        if not isinstance(calendar,dict) or not isinstance(calendar.get("earningsCalendar"),list):
            raise ValueError("INVALID_EARNINGS_CALENDAR")
        result["earnings_status"] = "FETCHED" if calendar["earningsCalendar"] else "EMPTY_UNVERIFIED"
        result["earnings_dates"] = [{"date":x.get("date"),"hour":x.get("hour")}
                                    for x in calendar["earningsCalendar"]
                                    if isinstance(x,dict) and x.get("symbol","").upper()==symbol.upper()]
    except Exception as exc:
        result["earnings_status"] = "FAILED: "+type(exc).__name__
    result["status"] = ("REVIEW_NEWS_AND_EARNINGS" if result["headline_review"] or result["earnings_dates"]
                        else "NO_VERIFIED_EVENT_CLEARANCE")
    result["reason"] = "News/calendar are incomplete signals, not proof of absence of events or corporate actions"
    return result

