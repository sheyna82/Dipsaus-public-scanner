"""Privacy-preserving research evidence manifest.

A digest proves only that a later byte sequence matches the recorded
sequence; it does not authenticate source identity or market correctness.
Never store broker screenshots, account details, tokens or raw quotes here.
"""
import hashlib
import json
import re
from datetime import datetime, timezone

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}
GROUPS = ("broker_quote", "technical_levels", "fees", "fx", "slippage")


def _timestamp(value):
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc) if dt.utcoffset() is not None else None
    except (TypeError, ValueError, OverflowError):
        return None


def build_manifest(attestations, *, instrument_id, market, now=None):
    """Return metadata-only manifest; no raw prices or account identifiers.

    Caller must provide an opaque, non-identifying instrument_id (e.g. public
    ISIN); the function rejects source URLs, arbitrary metadata and raw fields.
    """
    now = datetime.now(timezone.utc) if now is None else now
    if not isinstance(now, datetime) or now.utcoffset() is None:
        return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_CLOCK"}
    if market not in ("EU", "US") or not isinstance(instrument_id, str):
        return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_INSTRUMENT"}
    # Restrict to public ISIN syntax; not a broker account identifier.
    if re.fullmatch(r"[A-Z]{2}[A-Z0-9]{10}", instrument_id) is None:
        return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_INSTRUMENT"}
    if not isinstance(attestations, dict) or set(attestations) != set(GROUPS):
        return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_GROUPS"}
    groups = []
    for name in GROUPS:
        entry = attestations[name]
        if not isinstance(entry, dict) or set(entry) != {"source_class", "observed_utc", "verified", "digest_sha256"}:
            return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "UNSAFE_FIELDS", "group": name}
        if entry["source_class"] not in ("BROKER", "PUBLIC_PROVIDER", "EXCHANGE", "ISSUER", "MANUAL_RESEARCH"):
            return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_SOURCE_CLASS", "group": name}
        if type(entry["verified"]) is not bool:
            return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_VERIFICATION", "group": name}
        timestamp = _timestamp(entry["observed_utc"])
        if timestamp is None or (now.astimezone(timezone.utc)-timestamp).total_seconds() < -30:
            return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_TIMESTAMP", "group": name}
        digest = entry["digest_sha256"]
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            return {**BLOCKED, "status": "MANIFEST_BLOCKED", "reason": "INVALID_DIGEST", "group": name}
        groups.append({"group": name, "source_class": entry["source_class"],
                       "observed_utc": timestamp.isoformat(),
                       "verified_claim": entry["verified"], "digest_sha256": digest})
    result = {"schema_version": 1, "market": market, "instrument_isin": instrument_id,
              "groups": groups, "trade_ready": False, "order_placement_enabled": False,
              "source_authenticity_independently_verified": False,
              "status": "METADATA_ONLY_UNAUTHENTICATED"}
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":")).encode("utf-8")
    result["manifest_sha256"] = hashlib.sha256(encoded).hexdigest()
    return result
