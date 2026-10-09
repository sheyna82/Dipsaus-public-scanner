"""Independent intraday confirmation research; Yahoo quotes may be delayed. Never generate orders."""
import json,math,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from zoneinfo import ZoneInfo
ROOT=Path("reports")
def fetch(symbol,interval,range_):
    url="https://query1.finance.yahoo.com/v8/finance/chart/"+urllib.parse.quote(symbol,safe="")+"?"+urllib.parse.urlencode({"range":range_,"interval":interval})
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0","Accept":"application/json","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=20) as f: payload=json.load(f)
    result=(payload.get("chart",{}).get("result") or [None])[0]
    if not result:raise ValueError("Missing chart result: "+str(payload.get("chart",{}).get("error")))
    meta=result["meta"];tz=ZoneInfo(meta["exchangeTimezoneName"])
    if meta.get("symbol")!=symbol:raise ValueError("Symbol mismatch")
    quote=result["indicators"]["quote"][0];bars=[]
    for i,stamp in enumerate(result.get("timestamp") or []):
        try:
            o,h,l,c,v=[quote[k][i] for k in ("open","high","low","close","volume")]
            if not all(isinstance(x,(int,float)) and math.isfinite(x) for x in (o,h,l,c,v)):continue
            if l<=0 or l>min(o,c) or max(o,c)>h or v<0:continue
            bars.append({"time":datetime.fromtimestamp(stamp,timezone.utc).astimezone(tz).isoformat(),"open":o,"high":h,"low":l,"close":c,"volume":v})
        except (IndexError,KeyError,TypeError,ValueError):continue
    return meta,bars
def main():
    report=json.loads((ROOT/"europe_swing_research.json").read_text())
    # Investigate early recovery ideas BEFORE strict historical research gates.
    candidates=[r for r in report["candidates"]
                if r.get("historical_close",0)>0
                and r.get("calendar_days_old",999)<=4
                and r.get("drawdown_126d_pct",0)<=-10
                and r.get("signal_count",0)>=1]
    # Scan EVERY discovery-eligible name intraday. A hard 24-name cap previously hid
    # valid recoveries simply because they lost a sector-rotation lottery.
    candidates.sort(key=lambda r:(r.get("signal_count",0),-r.get("drawdown_126d_pct",0)),reverse=True)
    watchlist_count=len(candidates)
    deferred=[]
    output=[]
    print("WATCHLIST-ELIGIBLE",watchlist_count,"INTRADAY-CHECKED",len(candidates),flush=True)
    for row in candidates:
        sym=row["symbol"];result={"symbol":sym,"historical_reference":row.get("historical_close"),"historical_status":row.get("status"),"historical_research_flags":row.get("research_flags"),"research_only":True,
                                  "trade_ready":False,"broker_quote_verified":False,"spread_verified":False,
                                  "portfolio_fit_verified":False,"news_verified":False,"execution_blocked":True}
        try:
            meta,bars=fetch(sym,"15m","5d")
            result.update(currency=meta.get("currency"),exchange=meta.get("exchangeName"),timezone=meta.get("exchangeTimezoneName"),
                          provider="Yahoo Finance chart",provider_delay_not_verified=True,
                          latest_bar=bars[-1] if bars else None,valid_15m_bars=len(bars))
            if len(bars)<15:raise ValueError("Insufficient 15-minute history")
            day=bars[-1]["time"][:10];today=[b for b in bars if b["time"][:10]==day]
            # Session-adaptive confirmation: at the European open there cannot yet be
            # three completed 15m bars. Do not turn that clock fact into DATA-BLOCKED.
            # Use the bars that actually exist and mark confidence explicitly.
            if len(today)<1:raise ValueError("No intraday bar in latest exchange-local day")
            prior=[b for b in bars if b["time"][:10]!=day]
            lows=[b["low"] for b in today];closes=[b["close"] for b in today]
            highs=[b["high"] for b in today]
            higher_last_low=(lows[-1]>lows[-2]) if len(today)>=2 else None
            above_prior_bar_high=(closes[-1]>today[-2]["high"]) if len(today)>=2 else None
            recent3=today[-3:]
            holding_low=(min(b["low"] for b in recent3) > min(lows[:-3])) if len(today)>=6 else None
            reclaim=(closes[-1] > max(b["high"] for b in today[-4:-1])) if len(today)>=4 else None
            above_open=closes[-1] > today[0]["open"]
            # Before 3 bars, combine available same-session evidence with a conservative
            # prior-session reference. This is discovery/pre-alert evidence only.
            prior_close=prior[-1]["close"] if prior else None
            above_prior_close=(closes[-1]>prior_close) if prior_close is not None else None
            evidence=[x for x in (higher_last_low,above_prior_bar_high,holding_low,reclaim,above_open,above_prior_close) if x is not None]
            early_recovery_score=sum(x is True for x in evidence)
            session_phase="OPENING" if len(today)<3 else ("EARLY" if len(today)<6 else "ESTABLISHED")
            min_structure_score=1 if len(today)<3 else 2
            result.update(latest_session_date=day,latest_session_bars=len(today),
                          latest_session_low=min(lows),latest_session_high=max(b["high"] for b in today),
                          latest_close=closes[-1],last_three_lows=[round(x,4) for x in lows[-3:]],
                          higher_last_low=higher_last_low,above_prior_bar_high=above_prior_bar_high,
                          holding_recent_low=holding_low,reclaim_recent_range=reclaim,above_session_open=above_open,
                          above_prior_session_close=above_prior_close,session_phase=session_phase,
                          minimum_structure_score=min_structure_score,early_recovery_score=early_recovery_score,
                          above_session_vwap_proxy=None,
                          data_status="INTRADAY-RESEARCH-ONLY",
                          note="15m bars may be delayed/incomplete. No broker quote, verified delay, corporate actions, spread or executable trigger.")
        except Exception as exc:result.update(data_status="DATA-BLOCKED",reason=type(exc).__name__)
        output.append(result)
        print(json.dumps({"symbol":sym,"sector":row.get("sector"),
                          "historical_status":result.get("historical_status"),
                          "historical_flags":result.get("historical_research_flags"),
                          "intraday_status":result["data_status"],
                          "bar_time":(result.get("latest_bar") or {}).get("time"),
                          "currency":result.get("currency"),
                          "last_close":result.get("latest_close"),
                          "session_low":result.get("latest_session_low"),
                          "session_high":result.get("latest_session_high"),
                          "higher_last_low":result.get("higher_last_low"),
                          "above_prior_bar_high":result.get("above_prior_bar_high"),
                          "holding_recent_low":result.get("holding_recent_low"),
                          "reclaim_recent_range":result.get("reclaim_recent_range"),
                          "early_recovery_score":result.get("early_recovery_score"),
                          "reason":result.get("reason"),
                          "trade_ready":False},ensure_ascii=False),flush=True)
    summary={"generated_utc":datetime.now(timezone.utc).isoformat(),"source_report_generated_utc":report.get("generated_utc"),
             "scope":"All discovery-eligible names from the expanded European universe receive intraday confirmation; NOT market-wide and provider data is never executable.",
             "watchlist_eligible_count":watchlist_count,"candidate_count":len(candidates),"deferred_count":len(deferred),"deferred_symbols":deferred,"checked_count":len(output),"trade_ready_count":0,
             "candidates":output}
    (ROOT/"europe_intraday_confirmation.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in summary.items() if k!="candidates"},indent=2))
if __name__=="__main__":main()

