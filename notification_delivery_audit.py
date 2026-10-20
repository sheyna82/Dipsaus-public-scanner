"""Aggregate-only audit of notification state; does not send or read secrets."""
from collections import Counter

VALID = frozenset({"reserved", "sent", "rejected", "uncertain"})

def audit_delivery_state(state):
    if not isinstance(state, dict) or not isinstance(state.get("signals"), dict):
        raise ValueError("notification state unavailable")
    counts = Counter()
    for record in state["signals"].values():
        if not isinstance(record, dict):
            raise ValueError("notification record invalid")
        status = record.get("delivery")
        if status not in VALID:
            counts["unknown"] += 1
        else:
            counts[status] += 1
    return {
        "records": len(state["signals"]),
        "sent_to_provider": counts["sent"],
        "reserved": counts["reserved"],
        "rejected": counts["rejected"],
        "uncertain": counts["uncertain"],
        "unknown": counts["unknown"],
        "phone_receipt_verified": False,
        "delivery_verified": False,
    }
