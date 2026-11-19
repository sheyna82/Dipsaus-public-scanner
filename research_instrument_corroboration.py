"""Offline research cross-check of instrument claims from distinct source classes.

No live registry retrieval or cryptographic source authentication is performed.
Provider and broker assertions must never be promoted into exchange attestation.
"""
import re
from datetime import datetime, timezone
from research_instrument_gate import isin_checksum_valid

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}
ALLOWED = frozenset(("EXCHANGE", "OFFICIAL_MIC_REGISTER", "BROKER"))


def _stamp(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.utcoffset() is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def compare_instrument_records(records, *, now=None):
    """Require two distinct institutional claims and a separate broker route.

    Expected records: EXCHANGE listing, OFFICIAL_MIC_REGISTER venue, BROKER
    route. A passing result is only a consistent evidence package, not proof
    that the named sources are genuine or that an order can be executed.
    """
    blocked = {**BLOCKED, "status": "INSTRUMENT_EVIDENCE_BLOCKED",
               "source_authenticity_independently_verified": False}
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.utcoffset() is None:
        return {**blocked, "reason": "INVALID_CLOCK"}
    if not isinstance(records, list) or len(records) != 3:
        return {**blocked, "reason": "RECORD_COUNT"}
    groups = {}
    ids = set()
    for row in records:
        if not isinstance(row, dict) or row.get("source_class") not in ALLOWED:
            return {**blocked, "reason": "SOURCE_CLASS"}
        cls = row["source_class"]
        if cls in groups:
            return {**blocked, "reason": "DUPLICATE_SOURCE_CLASS"}
        sid = row.get("source_id")
        if not isinstance(sid, str) or not sid.strip() or len(sid) > 256 or sid in ids:
            return {**blocked, "reason": "SOURCE_ID"}
        ids.add(sid)
        if row.get("verified") is not True:
            return {**blocked, "reason": "UNVERIFIED_RECORD"}
        stamp = _stamp(row.get("observed_utc"))
        if stamp is None or not -30 <= (now.astimezone(timezone.utc)-stamp).total_seconds() <= 86400:
            return {**blocked, "reason": "STALE_RECORD"}
        mic = row.get("operating_mic")
        if not isinstance(mic, str) or re.fullmatch(r"[A-Z0-9]{4}", mic) is None:
            return {**blocked, "reason": "INVALID_IDENTITY"}
        # ISO 10383 registers venues/MICs, not per-instrument ISIN listings.
        if cls != "OFFICIAL_MIC_REGISTER" and not isin_checksum_valid(row.get("isin")):
            return {**blocked, "reason": "INVALID_IDENTITY"}
        if cls == "OFFICIAL_MIC_REGISTER" and "isin" in row:
            return {**blocked, "reason": "REGISTRY_MUST_NOT_ASSERT_ISIN"}
        if row.get("active") is not True:
            return {**blocked, "reason": "INACTIVE_OR_UNVERIFIED"}
        if cls == "EXCHANGE" and (not isinstance(row.get("segment"), str) or not row["segment"].strip()):
            return {**blocked, "reason": "MISSING_SEGMENT"}
        if cls == "BROKER" and row.get("route_verified") is not True:
            return {**blocked, "reason": "BROKER_ROUTE_BLOCKED"}
        groups[cls] = row
    if set(groups) != ALLOWED:
        return {**blocked, "reason": "MISSING_SOURCE_CLASS"}
    if len({row["operating_mic"] for row in records}) != 1 or groups["EXCHANGE"]["isin"] != groups["BROKER"]["isin"]:
        return {**blocked, "reason": "IDENTITY_CONFLICT"}
    return {**BLOCKED, "status": "CROSS_SOURCE_CLAIMS_CONSISTENT",
            "isin": groups["EXCHANGE"]["isin"], "operating_mic": groups["EXCHANGE"]["operating_mic"],
            "segment_claim": groups["EXCHANGE"]["segment"],
            "source_authenticity_independently_verified": False,
            "warning": "Metadata-only corroboration; no direct official registry or broker API authentication."}
