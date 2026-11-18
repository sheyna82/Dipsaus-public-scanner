"""Pure offline bridge from normalized aggregate bars to strict forward research.

Massive aggregate timestamp 'time' denotes the aggregate start, NOT its end.
A caller must provide separately attested completed-bar end and observed times.
No inference from the provider's start timestamp; no network or production IO.
"""
from datetime import datetime, timezone
from research.us_strict_forward_evidence_20261118 import evaluate_strict_forward

def _parse(s):
    if not isinstance(s, str):
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, OverflowError):
        return None

def bridge_normalized_bars(snapshot, normalized, receipts):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if (not isinstance(normalized, dict) or normalized.get("status") != "NORMALIZED_UNVERIFIED"
            or normalized.get("provider_id") != "massive"
            or not isinstance(normalized.get("bars"), list)
            or not isinstance(receipts, list)
            or len(normalized["bars"]) != len(receipts)):
        return {**base, "blocks": ["BAR_OR_RECEIPT_SET_INVALID"]}
    bars = []
    for i, (bar, receipt) in enumerate(zip(normalized["bars"], receipts)):
        if not isinstance(bar, dict) or not isinstance(receipt, dict):
            return {**base, "blocks": ["BAR_OR_RECEIPT_INVALID"], "invalid_index": i}
        start, end, observed = (_parse(bar.get("time")),
                                _parse(receipt.get("bar_end_utc")),
                                _parse(receipt.get("observed_utc")))
        if (start is None or end is None or observed is None
                or not start < end <= observed
                or receipt.get("source_bar_start_utc") != bar.get("time")):
            return {**base, "blocks": ["BAR_COMPLETION_PROVENANCE_INVALID"], "invalid_index": i}
        bars.append({"bar_end_utc": receipt["bar_end_utc"],
                     "observed_utc": receipt["observed_utc"], "close_usd": bar.get("close")})
    result = evaluate_strict_forward(snapshot, bars)
    return {**result, "blocks": sorted(set(result.get("blocks", []) +
            ["RECEIPT_INDEPENDENCE_NOT_ATTESTED", "SOURCE_AUTHENTICITY_NOT_ATTESTED"])),
            "limitations": ["Aggregate start is not bar end",
                            "Receipts supplied by caller; independent verification absent",
                            "No provider or broker access"]}
