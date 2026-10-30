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

def eligible_replay(case, *, alert_timestamp=None, timestamped_bars=None,
                    signal_snapshot=None, alert_evidence=None, price_evidence=None):
    """Require independently timestamped evidence before any historical replay.

    This is an intake gate, NOT a profitability test or a trading signal.
    """
    if case not in CASES:
        return False
    if not (alert_timestamp and timestamped_bars and signal_snapshot):
        return False
    if not isinstance(alert_evidence, dict) or not isinstance(price_evidence, dict):
        return False
    if alert_evidence.get("verified") is not True or not alert_evidence.get("source_id"):
        return False
    if price_evidence.get("verified") is not True or not price_evidence.get("source_id"):
        return False
    if not isinstance(alert_timestamp, datetime):
        return False
    if alert_timestamp.tzinfo is None or alert_timestamp.utcoffset() is None:
        return False
    if alert_timestamp.astimezone(ZoneInfo("America/New_York")).date().isoformat() != case["alert_date"]:
        return False
    if not isinstance(signal_snapshot, dict):
        return False
    created = signal_snapshot.get("created_at")
    if not isinstance(created, datetime) or created.tzinfo is None or created.utcoffset() is None:
        return False
    if created > alert_timestamp:
        return False
    # An alert is not a verified signal merely because it has a source label.
    if signal_snapshot.get("ticker") != case["ticker"]:
        return False
    if not signal_snapshot.get("source_id"):
        return False
    # Synthetic fixture flags must never be interpreted as independent verification.
    for evidence in (alert_evidence, price_evidence):
        if evidence.get("origin") != "independent_archive":
            return False
    if signal_snapshot.get("origin") != "independent_archive":
        return False
    if not isinstance(timestamped_bars, (tuple, list)) or not timestamped_bars:
        return False
    last = alert_timestamp
    for bar in timestamped_bars:
        if not isinstance(bar, dict):
            return False
        stamp = bar.get("timestamp")
        if not isinstance(stamp, datetime) or stamp.tzinfo is None or stamp.utcoffset() is None:
            return False
        if stamp <= last:
            return False
        if not all(field in bar for field in ("open", "high", "low", "close", "volume")):
            return False
        try:
            from decimal import Decimal
            o, h, l, c, v = (Decimal(str(bar[key])) for key in ("open", "high", "low", "close", "volume"))
            if min(o, h, l, c) <= 0 or v < 0 or l > min(o, c) or h < max(o, c):
                return False
            if not all(x.is_finite() for x in (o, h, l, c, v)):
                return False
        except (ValueError, TypeError, ArithmeticError):
            return False
        last = stamp
    return True


if __name__ == "__main__":
    validate_cases()
    for case in CASES:
        print(case["ticker"], case["kind"], "REPLAY_BLOCKED_UNTIL_TIMESTAMPED_EVIDENCE")
