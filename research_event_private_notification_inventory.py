"""Private-state event notification audit. No private records are persisted.

Reads in-memory scanner state via existing verified_notification_times helper.
A notified timestamp is NOT proof of actual push delivery or a frozen signal.
"""
from research_notification_timestamp_extract import verified_notification_times
from research_event_replay_intake_202610 import CASES

def notification_evidence_inventory(state):
    wanted = {case["ticker"] for case in CASES}
    records = verified_notification_times(state, sorted(wanted))
    grouped = {ticker: [] for ticker in sorted(wanted)}
    for record in records:
        ticker = record["symbol"]
        grouped[ticker].append({
            "notified_utc": record["notification_utc"],
            "delivery_status": record["delivery_status"],
            "key_family": record["key_family"],
            "timestamp_origin": "private_scanner_state",
            "push_delivery_independently_verified": False,
            "signal_snapshot_independently_verified": False,
        })
    # Deduplicate repeated family/timestamp notifications without hiding duplicates.
    for ticker in grouped:
        seen = set()
        distinct = []
        for item in grouped[ticker]:
            key = (item["notified_utc"], item["key_family"])
            if key not in seen:
                seen.add(key)
                distinct.append(item)
        grouped[ticker] = distinct
    return {
        "cases": grouped,
        "missing_notification_timestamps": sorted(t for t in wanted if not grouped[t]),
        "historical_profit_claim_allowed": False,
        "delivery_proof_available": False,
        "private_state_exported": False,
    }
