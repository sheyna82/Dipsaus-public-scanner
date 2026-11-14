"""Fail-closed provenance gate for historical ex-ante selection evidence."""
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

def _timestamp(value):
    if not isinstance(value, str):
        raise ValueError("INVALID_TIMESTAMP")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("INVALID_TIMESTAMP")
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return dt.astimezone(timezone.utc)

def validate(records):
    if not isinstance(records, list):
        raise ValueError("INVALID_RECORDS")
    verified = []
    seen = set()
    for row in records:
        ident = row["id"]
        if ident in seen:
            raise ValueError("DUPLICATE_REGISTRATION")
        seen.add(ident)
        registered = _timestamp(row["registered_at"])
        available = _timestamp(row["source_available_at"])
        entry = _timestamp(row["entry_at"])
        if not (available <= registered < entry):
            raise ValueError("POINT_IN_TIME_VIOLATION")
        if row.get("source_verified") is not True or row.get("immutable_registration_verified") is not True:
            raise ValueError("UNVERIFIED_PROVENANCE")
        if not isinstance(row.get("source_sha256"), str) or len(row["source_sha256"]) != 64 or any(ch not in "0123456789abcdef" for ch in row["source_sha256"]):
            raise ValueError("INVALID_SOURCE_SHA256")
        if row.get("future_return") is not None or row.get("realized_pnl_eur") is not None:
            raise ValueError("OUTCOME_LEAKAGE")
        try:
            priority = Decimal(str(row["registered_priority"]))
        except (InvalidOperation, ValueError):
            raise ValueError("INVALID_PRIORITY")
        if not priority.is_finite():
            raise ValueError("INVALID_PRIORITY")
        verified.append({"id": ident, "registered_priority": float(priority),
                         "priority_source_verified": True,
                         "priority_registered_before_entry": True,
                         "research_only": True, "trade_ready": False})
    return {"status": "RESEARCH_ONLY_EX_ANTE_PROVENANCE_CHECK",
            "trade_ready": False, "historical_authenticity_independently_proven": False,
            "verified_registrations": verified,
            "limitations": ["boolean evidence claims require external artifact verification",
                            "source hashes are format-checked, not recomputed here"]}
