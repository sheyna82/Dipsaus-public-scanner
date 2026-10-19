"""Dated earnings reminders: issuer-confirmed dates plus provider-discovered estimates."""
from datetime import date, datetime, timezone, timedelta
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
from private_notifications import reserve_send

# Only dates with cited official issuer pages; refresh after each event.
EVENTS = (
 ("TSLA","2026-10-21","Q3 results after US close","https://ir.tesla.com/"),
 ("META","2026-10-21","Q3 results","https://investor.atmeta.com/investor-events/"),
 ("COHU","2026-10-28","Q3 results after US close","https://ir.cohu.com/news-releases/news-release-details/cohu-announce-third-quarter-financial-results-october-28"),
 ("AMZN","2026-10-29","Q3 results after US close","https://ir.aboutamazon.com/events/default.aspx"),
 ("PLTR","2026-11-02","Q3 results after US close","https://investors.palantir.com/news-details/2026/Palantir-Announces-Date-of-Third-Quarter-2026-Earnings-Release-and-Webcast/"),
 ("AMD","2026-11-03","Q3 results after US close","https://ir.amd.com/news-events/press-releases/detail/1300/amd-to-report-fiscal-third-quarter-2026-financial-results"),
)

def due_events(today=None):
    today = today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    for symbol, iso, label, source in EVENTS:
        delta = (date.fromisoformat(iso) - today).days
        if delta in (1,0,-1):
            stage = "TOMORROW" if delta == 1 else "TODAY" if delta == 0 else "POST_EVENT"
            yield symbol, iso, label, source, stage

def discover_earnings(symbols, today=None, fetch=None):
    """Find next 21 days of earnings from Finnhub; provider dates are ESTIMATED.

    Never treat these as issuer-confirmed or an executable trading signal.
    Fail closed on network/API/format errors. One calendar query per refresh.
    """
    today = today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    token = os.environ.get("FINNHUB_API_KEY", "").strip()
    if fetch is None and not token:
        return []
    url = ("https://finnhub.io/api/v1/calendar/earnings?" +
           urllib.parse.urlencode({"from":today.isoformat(),
             "to":(today+timedelta(days=21)).isoformat(),"token":token}))
    try:
        if fetch is None:
            req=urllib.request.Request(url,headers={"User-Agent":"DIPSAUS event research"})
            with urllib.request.urlopen(req,timeout=12) as response:
                data=json.load(response)
        else:
            data=fetch(url)
        rows=data.get("earningsCalendar",[])
        if not isinstance(rows,list):
            return []
        allowed={x for x in symbols if isinstance(x,str) and re.fullmatch(r"[A-Z][A-Z0-9.\\-]{0,14}",x)}
        official={(sym,iso) for sym,iso,*_ in EVENTS}
        found={}
        for row in rows:
            if not isinstance(row,dict): continue
            sym=row.get("symbol");iso=row.get("date")
            if sym not in allowed or not isinstance(iso,str): continue
            try: day=date.fromisoformat(iso)
            except ValueError: continue
            if not today<=day<=today+timedelta(days=21) or (sym,iso) in official: continue
            found[(sym,iso)]=(sym,iso,"Earnings (provider estimate; verify issuer IR)",
                               "https://finnhub.io/", "ESTIMATED")
        return list(found.values())
    except (OSError,ValueError,TypeError,KeyError,TimeoutError):
        return []

def refresh_discovered_events(state, today=None, fetch=None):
    """Daily bounded provider refresh. Keep cached results on provider failure."""
    today=today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    cache=state.setdefault("company_event_calendar",{})
    if cache.get("checked_day")==today.isoformat():
        return cache.get("events",[])
    try:
        gate=json.loads(Path("config/notification_quality_gate.json").read_text())
        symbols=set(gate.get("auto_us_notify_watchlist",[]))
        symbols.update(gate.get("auto_us_silent_follow",[]))
    except (OSError,ValueError,TypeError):
        return cache.get("events",[])
    if not symbols:
        return cache.get("events",[])
    # Never overwrite a previous good calendar with a provider outage.
    events=discover_earnings(symbols,today,fetch=fetch)
    if events:
        cache.update(checked_day=today.isoformat(),events=events)
    return events or cache.get("events",[])

def due_discovered_events(state,today=None):
    today=today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()
    for row in refresh_discovered_events(state,today):
        try:
            sym,iso,label,source,status=row
            delta=(date.fromisoformat(iso)-today).days
        except (ValueError,TypeError):
            continue
        if delta in (1,0,-1):
            stage="TOMORROW" if delta==1 else "TODAY" if delta==0 else "POST_EVENT"
            yield sym,iso,label,source,stage,status

def notify_events(store,state,sender=None,today=None):
    """Research reminders, NEVER trade-ready signals. Persist per-event-stage dedupe."""
    store.require_exclusive_sender()
    signals=state.setdefault("signals",{})
    scheduled=[(*event,"ISSUER_CONFIRMED") for event in due_events(today)]
    scheduled.extend(due_discovered_events(state,today))
    for symbol,iso,label,source,stage,confidence in scheduled:
        key=f"EVENT|{symbol}|{iso}|{stage}"
        if key in signals:
            continue
        record={"day":(today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()).isoformat(),
                "event_date":iso,"event_stage":stage,"event_confidence":confidence,"notification_schema_version":2,
                "notified_utc":datetime.now(timezone.utc).isoformat()}
        body=(f"{symbol}: BEDRIJFSGEBEURTENIS {stage} - {iso}: {label}. "
              f"Status: {confidence}. Bron: {source}. Controleer datum bij issuer IR, actuele koers, nieuws, uitkomst en spread. "
              "Geen koopbevestiging; pas na bevestigde structuur, R/R en bruto EUR3500-kans. "
              "Geen automatische order.")
        reserve_send(store,state,key,record,symbol,body,sender)
