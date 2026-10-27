"""Point-in-time event replay intake. No prices, fills or PnL are inferred."""
from datetime import datetime
from zoneinfo import ZoneInfo

CASES = (
    {"ticker": "TSLA", "event_date": "2026-10-21", "kind": "POST_EVENT", "alert_date": "2026-10-22", "event_source": "https://giroku.app/earnings"},
    {"ticker": "META", "event_date": "2026-10-21", "kind": "POST_EVENT", "alert_date": "2026-10-22", "event_source": "https://investor.atmeta.com/investor-news/press-release-details/2026/Meta-to-Announce-Third-Quarter-2026-Results/default.aspx"},
    {"ticker": "COHU", "event_date": "2026-10-28", "kind": "PRE_EVENT", "alert_date": "2026-10-22", "event_source": "https://ir.cohu.com/node/5816"},
    {"ticker": "AMZN", "event_date": "2026-10-29", "kind": "PRE_EVENT", "alert_date": "2026-10-22", "event_source": "https://www.aboutamazon.com/news/company-news/amazon-earnings-q3-2026-report"},
)
# Alert date is from prior conversation reconstruction, not a verified delivery timestamp.
# Screenshots dated Oct 27 are retrospective observations, never point-in-time features.
ALERT_PROVENANCE = "conversation_reconstruction_unverified_delivery_time"
PRICE_PROVENANCE = "screenshots_only_no_machine_readable_ohlcv"

def validate_cases(cases=CASES):
    seen = set()
    for case in cases:
        ticker = case["ticker"]
        if ticker in seen:
            raise ValueError("duplicate ticker")
        seen.add(ticker)
        event = datetime.fromisoformat(case["event_date"]).date()
        alert = datetime.fromisoformat(case["alert_date"]).date()
        expected = "PRE_EVENT" if alert < event else "POST_EVENT"
        if case["kind"] != expected:
            raise ValueError(f"{ticker}: event classification conflicts with alert date")
        if not case["event_source"].startswith("https://"):
            raise ValueError(f"{ticker}: missing source")
    return True

def eligible_replay(case, *, alert_timestamp=None, timestamped_bars=None, signal_snapshot=None):
    """Fail closed: date-only alert and screenshot prices cannot produce a trade."""
    if not (alert_timestamp and timestamped_bars and signal_snapshot):
        return False
    if alert_timestamp.tzinfo is None:
        return False
    if not isinstance(signal_snapshot, dict) or signal_snapshot.get("created_at") is None:
        return False
    created = signal_snapshot["created_at"]
    if created.tzinfo is None or created > alert_timestamp:
        return False
    return all(bar.get("timestamp") is not None and
               bar["timestamp"].tzinfo is not None and
               bar["timestamp"] >= alert_timestamp
               for bar in timestamped_bars)

if __name__ == "__main__":
    validate_cases()
    for case in CASES:
        print(case["ticker"], case["kind"], "REPLAY_BLOCKED_UNTIL_TIMESTAMPED_EVIDENCE")
