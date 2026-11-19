"""Deterministic offline receipt for EU research evidence inputs.

Hashes the exact canonical evidence payload, not external market data. A
receipt establishes local reproducibility, never source authenticity.
"""
import hashlib
import json
from datetime import datetime, timezone

ROLES = ("ask", "target_bid", "invalidation", "fx", "fees")
SCHEMA = "spoor2-eu-evidence-receipt-v1"

def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")

def build_eu_evidence_receipt(candidate, *, captured_utc):
    blocked = {"status": "BLOCKED", "trade_ready": False,
               "order_placement_enabled": False}
    if not isinstance(candidate, dict) or not isinstance(captured_utc, datetime) or captured_utc.tzinfo is None:
        return {**blocked, "blocks": ["INVALID_RECEIPT_INPUT"]}
    if any(not isinstance(candidate.get(role + "_evidence"), dict) for role in ROLES):
        return {**blocked, "blocks": ["EVIDENCE_RECORD_MISSING"]}
    try:
        # No floats: JSON float serialization is not an auditable financial
        # representation. All numeric prices/rates must be decimal strings.
        def reject_floats(value):
            if isinstance(value, float):
                raise ValueError("FLOAT_NOT_ALLOWED")
            if isinstance(value, dict):
                for k, v in value.items():
                    if not isinstance(k, str):
                        raise ValueError("NON_STRING_KEY")
                    reject_floats(v)
            elif isinstance(value, list):
                for v in value:
                    reject_floats(v)
        reject_floats(candidate)
        raw = _canonical(candidate)
    except (TypeError, ValueError, OverflowError, RecursionError):
        return {**blocked, "blocks": ["NONCANONICAL_EVIDENCE"]}
    return {**blocked, "status": "LOCAL_RECEIPT_ONLY",
            "schema": SCHEMA,
            "captured_utc": captured_utc.astimezone(timezone.utc).isoformat(),
            "payload_sha256": hashlib.sha256(raw).hexdigest(),
            "payload_bytes": len(raw),
            "record_roles": list(ROLES),
            "blocks": ["EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED"],
            "integrity_scope": "canonical supplied JSON only; no external retrieval, timestamp authority, or provider signature"}
