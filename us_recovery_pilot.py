"""Bounded US recovery discovery pilot. Research only, never trade-ready."""
import csv, io, json, math, os, re, time, urllib.request
from datetime import datetime, timezone
from pathlib import Path
from us_recovery_map import recovery_map
from us_event_research import ticker_ciks, filing_review, filing_content_review
from us_news_fallback import fallback_news
from us_research_triage import research_queue
from us_candidate_dossier import dossier
from us_company_profile import company_profile
from us_identity_check import identity_check
from us_news_relevance import classify_headlines, classify_event_materiality

OUT = Path("reports"); OUT.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DipsausPilot/0.1)"}
SOURCES = {
    "nasdaq": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
    "other": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
}
LIMIT = 240
# Current-security identity boundary for reused tickers.
LISTING_START={"SPCX":"2026-06-12"}

def parse_batch(value):
    if value is None or not re.fullmatch(r"(?:0|[1-9]|1[0-9]|20)", value):
        raise ValueError("US_BATCH must be an explicitly supplied integer from 0 through 20")
    return int(value)

BATCH = None
BATCH_COUNT = 21
EXCLUDE = re.compile(r"\b(?:warrants?|rights?|units?|preferred|preference|depositary shares|notes?|bonds?|etns?|etfs?|funds?|trusts?|acquisition corp(?:oration)?|blank.check|spac|closed.end|convertible|debentures?|subscription|contingent value|beneficial interest|income fund|investment fund)\b", re.I)
EQUITY = re.compile(r"\b(?:common stock|common shares?|ordinary shares?|class [a-z] (?:common )?(?:stock|shares?)|american depositary (?:shares?|receipts?)|ads|adr)\b", re.I)

def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=20) as response:
        return response.read().decode("utf-8-sig")

def universe():
    selected, counts, errors, rejected = [], {}, {}, {}
    for name, url in SOURCES.items():
        try:
            rows = csv.DictReader((line for line in get(url).splitlines() if not line.startswith("File Creation Time")), delimiter="|")
            count = 0; reasons = {}
            for r in rows:
                symbol = (r.get("Symbol") or r.get("NASDAQ Symbol") or r.get("ACT Symbol") or "").strip()
                title = (r.get("Security Name") or "").strip()
                reason = None
                if r.get("Test Issue") != "N": reason = "test_or_unknown"
                elif r.get("ETF") != "N": reason = "etf_or_unknown"
                elif not re.fullmatch(r"[A-Z]{1,5}", symbol): reason = "unsupported_symbol"
                elif EXCLUDE.search(title): reason = "security_type"
                elif not EQUITY.search(title): reason = "unverified_equity_type"
                if reason:
                    reasons[reason] = reasons.get(reason, 0) + 1; continue
                count += 1; selected.append({"symbol": symbol, "name": title, "source": name})
            counts[name] = count; rejected[name] = reasons
        except Exception as exc: errors[name] = type(exc).__name__
    return sorted({r["symbol"]: r for r in selected}.values(), key=lambda r:r["symbol"]), counts, errors, rejected

def bars(symbol):
    url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol + "?range=6mo&interval=1d"
    result = json.loads(get(url))["chart"]["result"][0]; q = result["indicators"]["quote"][0]; rows = []
    for t, o, h, l, c, v in zip(result["timestamp"], q["open"], q["high"], q["low"], q["close"], q["volume"]):
        if any(x is None or not math.isfinite(float(x)) for x in (o,h,l,c,v)): continue
        if min(o,h,l,c) <= 0 or v <= 0: continue
        rows.append({"date":datetime.fromtimestamp(t,timezone.utc).date().isoformat(),"open":o,"high":h,"low":l,"close":c,"volume":v})
    start=LISTING_START.get(symbol)
    if start is not None: rows=[r for r in rows if r["date"]>=start]
    return rows

def assess(rows):
    if len(rows)<65: return None
    last=rows[-1]; low=min(x["low"] for x in rows); high=max(x["high"] for x in rows)
    recent=rows[-20:]; prior=rows[-40:-20]; short=rows[-6:]
    prior_low=min(x["low"] for x in prior); recent_low=min(x["low"] for x in recent)
    avg20=sum(x["close"] for x in recent)/20; avg_volume=sum(x["volume"] for x in rows[-21:-1])/20
    drawdown=(low/high-1)*100; rebound=(last["close"]/low-1)*100
    # Early-turn signals deliberately do not require a completed weekly confirmation.
    # This layer is discovery only; execution remains fail-closed downstream.
    recent_5d_low=min(x["low"] for x in short[:-1]); prior_5d_low=min(x["low"] for x in rows[-11:-6])
    signals={
        "higher_recent_low":recent_low>prior_low,
        "higher_5d_low":recent_5d_low>prior_5d_low,
        "close_above_20d_average":last["close"]>avg20,
        "positive_5d_change":last["close"]>rows[-6]["close"],
        "positive_2d_change":last["close"]>rows[-3]["close"],
        "volume_above_20d_average":last["volume"]>avg_volume,
    }
    early_turn=(signals["higher_5d_low"] and (signals["positive_2d_change"] or signals["positive_5d_change"]))
    established_turn=(signals["close_above_20d_average"] and signals["positive_5d_change"])
    signal_count=sum(signals.values())
    pre_screen_match=drawdown<=-20 and 1.5<=rebound<=35 and (early_turn or established_turn or signal_count>=3)
    return {"last_bar_date":last["date"],"last_close_usd":round(last["close"],3),"six_month_high":round(high,3),"six_month_low":round(low,3),"drawdown_pct":round(drawdown,2),"rebound_from_low_pct":round(rebound,2),"signals":signals,"early_turn":early_turn,"established_turn":established_turn,"signal_count":signal_count,"last_volume_shares":round(last["volume"]),"average_20d_volume_shares":round(avg_volume),"pre_screen_match":pre_screen_match}

def main():
    batch = parse_batch(os.environ.get("US_BATCH")); print("US_BATCH_REQUESTED:", batch, flush=True)
    universe_rows, counts, errors, rejected=universe()
    if errors or not universe_rows: raise RuntimeError("US_UNIVERSE_INVALID: source error or zero eligible equities; refusing green research run")
    n=min(LIMIT,len(universe_rows)); sample=universe_rows[batch::BATCH_COUNT][:n]
    report={"run_utc":datetime.now(timezone.utc).isoformat(),"status":"BOUNDED_RESEARCH_PILOT","source":"Nasdaq Trader official lists + Yahoo public historical daily chart","selection_method":"Rotating interleaved alphabetic batch; full 21-batch universe scheduled every US trading day; NOT sector-stratified","batch_index":batch,"batch_count":BATCH_COUNT,"filtered_list_counts":counts,"excluded_by_reason":rejected,"list_errors":errors,"filtered_unique_symbols":len(universe_rows),"requested_symbols":len(sample),"actual_symbols_screened":0,"failures":{},"sample_symbols":[x["symbol"] for x in sample],"candidates":[],"full_us_scan_executed":False,"promoted_candidates_complete":False,"new_buy_valid":False,"trade_ready":False,"recovery_map_version":"historical_daily_weekly_pivots_v2_early_turn_discovery","limitations":"Discovery only. Early turns intentionally surface before weekly confirmation. Identity/event/broker/money-RR/portfolio gates remain fail-closed for execution."}
    try:
        for item in sample:
            symbol=item["symbol"]
            try:
                rows=bars(symbol); result=assess(rows)
                if result is None: raise ValueError("INSUFFICIENT_VALID_DAILY_BARS")
                report["actual_symbols_screened"]+=1
                if result["pre_screen_match"]: report["candidates"].append({**item,**result,"recovery_map":recovery_map(rows, six_month_high=result["six_month_high"])})
            except Exception as exc: report["failures"][symbol]=type(exc).__name__
            time.sleep(0.35)
    finally:
        report["candidates"].sort(key=lambda x:(not x.get("early_turn",False),-x["signal_count"],x["symbol"]))
        for candidate in report["candidates"]:
            m=candidate["recovery_map"]; close=candidate["last_close_usd"]; friction=m["first_friction_reference_usd"]; zones=m["historical_overhead_pivot_zones"]; first_zone=zones[0]["low_usd"] if zones else None
            overhead=min(x for x in (friction,first_zone) if x is not None) if (friction is not None or first_zone is not None) else None
            space=round(100*(overhead/close-1),2) if overhead else None; weekly=m["weekly_structure"]
            candidate["research_triage"]={"first_overhead_reference_usd":overhead,"space_to_first_overhead_pct":space,"weekly_close_rising":weekly["completed_week_close_rising"],"weekly_higher_low":weekly["completed_week_higher_low"],"bottom_signal_count":m["bottom_signal_count"],"early_turn":candidate.get("early_turn",False),"company_event_risk_status":"NOT_CHECKED","corporate_actions_status":"NOT_CHECKED","sector_status":"UNVERIFIED","portfolio_fit_status":"NOT_CHECKED","broker_price_status":"NOT_CHECKED","first_overhead_status":"HISTORICAL_REFERENCE_NOT_VALIDATED","status":"EARLY_RECOVERY_RESEARCH_ONLY_NOT_TRADE_READY" if candidate.get("early_turn") else "RESEARCH_ONLY_NOT_TRADE_READY"}
        shortlist, queue_exclusions=research_queue(report["candidates"],limit=12)
        report["identity_shortlist"]=[]; priority=[]
        for candidate in shortlist:
            profile=company_profile(candidate["symbol"]); check=identity_check(candidate["symbol"],candidate["name"],profile)
            candidate["issuer_profile"]=profile; candidate["identity_crosscheck"]=check
            report["identity_shortlist"].append({"symbol":candidate["symbol"],"identity_status":check["status"],"profile_status":profile.get("status"),"reason":check["reason"]})
            if check["status"] != "IDENTITY_MISMATCH": priority.append(candidate)
            if len(priority)==3: break
        report["identity_queue_policy"]="At most twelve historically eligible candidates checked in order. Actual issuer mismatch blocks the queue; unavailable optional profile data stays visible and enters deep-dive with an explicit identity-verification block. Never execution-ready without identity clearance."
        report["identity_shortlist_exhausted"]=len(priority)<3
        report["deep_dive_queue"]=[dict(symbol=x["symbol"],name=x["name"],last_bar_date=x["last_bar_date"],research_triage=x["research_triage"],liquidity_triage=x["liquidity_triage"],weekly=x["recovery_map"]["weekly_structure"],pivot_zones=x["recovery_map"]["historical_overhead_pivot_zones"][:4],identity_status=x["identity_crosscheck"]["status"],profile_status=x["issuer_profile"].get("status"),status="MANUAL_COMPANY_EVENT_AND_BROKER_REVIEW_REQUIRED") for x in priority]
        report["queue_exclusions"]=queue_exclusions
        try: sec_ciks=ticker_ciks(); report["sec_ticker_map_status"]="FETCHED"
        except Exception as exc: sec_ciks={}; report["sec_ticker_map_status"]="FAILED: "+type(exc).__name__
        for queued in report["deep_dive_queue"]:
            event=filing_review(queued["symbol"],sec_ciks) if sec_ciks else {"source":"SEC EDGAR recent submissions","status":"SEC_TICKER_MAP_UNAVAILABLE","reason":report["sec_ticker_map_status"],"company_event_risk_verified":False,"corporate_actions_verified":False,"earnings_calendar_verified":False,"non_sec_events_verified":False,"recent_material_filing_signals":[]}
            event["filing_content_reviews"]=[filing_content_review(x) for x in event.get("recent_material_filing_signals",[])[:2]]
            queued["event_research"]=event; queued["alternative_event_research"]=fallback_news(queued["symbol"]) if event["status"] in ("SEC_TICKER_MAP_UNAVAILABLE","SEC_FETCH_FAILED","NO_SEC_TICKER_MATCH") else {"status":"NOT_NEEDED_SEC_AVAILABLE"}
            queued["review_decision"]="REVIEW_FILINGS_AND_EVENTS" if event["status"]=="FILING_REVIEW_REQUIRED" else "BLOCK_EVENT_CLEARANCE_PENDING"; queued["trade_ready"]=False
            candidate=next(x for x in report["candidates"] if x["symbol"]==queued["symbol"]); queued["research_dossier"]=dossier(candidate,queued)
            queued["research_dossier"]["news_relevance"]=classify_headlines(queued["alternative_event_research"],candidate["issuer_profile"]); queued["research_dossier"]["news_event_triage"]=classify_event_materiality(queued["research_dossier"]["news_relevance"]); queued["research_dossier"]["issuer_profile"]=candidate["issuer_profile"]; queued["research_dossier"]["identity_crosscheck"]=candidate["identity_crosscheck"]
            if queued["identity_status"]=="IDENTITY_UNVERIFIED": queued["review_decision"]="BLOCK_IDENTITY_AND_EVENT_CLEARANCE_PENDING"
        report["excluded_from_queue_due_to_near_overhead"]=queue_exclusions["near_overhead"]; report["queue_selection_limitations"]="Early technical recovery candidates survive optional profile/SEC outages, but identity, event, broker, money/RR and portfolio-fit gates remain fail-closed for execution."; report["deep_dive_queue_complete"]=False
        (OUT/"us_recovery_pilot.json").write_text(json.dumps(report,indent=2),encoding="utf-8"); print(json.dumps({k:v for k,v in report.items() if k!="candidates"},indent=2)); print("PRE-SCREEN CANDIDATES:",json.dumps(report["candidates"]))
    if report["actual_symbols_screened"]==0: raise RuntimeError("US_SCREEN_EMPTY: no valid daily histories; refusing green research run")
if __name__=="__main__": main()

