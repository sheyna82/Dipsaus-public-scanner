"""Verified dated event alerts. This is a curated calendar, NOT automatic discovery."""
from datetime import date, datetime, timezone
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

def notify_events(store,state,sender=None,today=None):
    """Research reminders, NEVER trade-ready signals. Persist per-event-stage dedupe."""
    store.require_exclusive_sender()
    signals=state.setdefault("signals",{})
    for symbol,iso,label,source,stage in due_events(today):
        key=f"EVENT|{symbol}|{iso}|{stage}"
        if key in signals:
            continue
        record={"day":(today or datetime.now(ZoneInfo("Europe/Amsterdam")).date()).isoformat(),
                "event_date":iso,"event_stage":stage,"notification_schema_version":1,
                "notified_utc":datetime.now(timezone.utc).isoformat()}
        body=(f"{symbol}: BEDRIJFSGEBEURTENIS {stage} - {iso}: {label}. "
              f"Bron: {source}. Controleer actuele koers, nieuws, uitkomst en spread. "
              "Geen koopbevestiging; pas na bevestigde structuur, R/R en bruto EUR3500-kans. "
              "Geen automatische order.")
        reserve_send(store,state,key,record,symbol,body,sender)
