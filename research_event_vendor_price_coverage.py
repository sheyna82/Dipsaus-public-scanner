"""Audit existing Stooq acquisition metadata against four event cases.

Vendor prices are NOT verified signals. Do not promote daily close prices into
an alert-time execution or infer a profitable historical trade.
"""
from datetime import date
from research_event_replay_intake_202610 import CASES

def audit_event_price_metadata(metadata):
    if not isinstance(metadata, list):
        raise TypeError("metadata_list_required")
    results = []
    for case in CASES:
        ticker = case["ticker"]
        matches = [row for row in metadata if isinstance(row, dict)
                   and row.get("symbol") == ticker]
        valid = []
        for row in matches:
            try:
                start = date.fromisoformat(row["first_observation_date"])
                end = date.fromisoformat(row["last_observation_date"])
                alert = date.fromisoformat(case["alert_date"])
                count = row["row_count"]
                if (start <= alert <= end and isinstance(count, int) and count > 0
                        and row.get("content_sha256") and row.get("source_url", "").startswith("https://")):
                    valid.append(row)
            except (KeyError, TypeError, ValueError):
                continue
        results.append({
            "ticker": ticker, "vendor_history_covers_alert_date": bool(valid),
            "vendor_metadata_records": len(matches),
            "vendor_source_independently_verified": False,
            "alert_timestamp_verified": False,
            "signal_snapshot_verified": False,
            "trade_ready": False,
        })
    return results
