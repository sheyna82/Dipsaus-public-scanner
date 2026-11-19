"""Independent, offline verification of a saved EU evidence receipt.

Reconstructs canonical bytes without calling the receipt builder. A matching
hash proves local byte-level consistency, NOT external source authenticity.
"""
import hashlib
import json
import re
from datetime import datetime, timezone

ROLES = ("ask", "target_bid", "invalidation", "fx", "fees")
SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
SCHEMA = "spoor2-eu-evidence-receipt-v1"

def verify_eu_evidence_receipt(payload, receipt):
    base = {"status": "BLOCKED", "receipt_verified": False,
            "trade_ready": False, "order_placement_enabled": False}
    if not isinstance(payload, dict) or not isinstance(receipt, dict):
        return {**base, "blocks": ["INVALID_VERIFICATION_INPUT"]}
    if receipt.get("schema") != SCHEMA:
        return {**base, "blocks": ["RECEIPT_SCHEMA_MISMATCH"]}
    if not isinstance(receipt.get("payload_sha256"), str) or not SHA256_HEX.fullmatch(receipt["payload_sha256"]):
        return {**base, "blocks": ["RECEIPT_DIGEST_INVALID"]}
    if any(not isinstance(payload.get(role + "_evidence"), dict) for role in ROLES):
        return {**base, "blocks": ["EVIDENCE_RECORD_MISSING"]}
    try:
        captured = receipt["captured_utc"]
        dt = datetime.fromisoformat(captured.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("naive timestamp")
    except (KeyError, TypeError, ValueError, AttributeError):
        return {**base, "blocks": ["RECEIPT_TIMESTAMP_INVALID"]}
    def check(value):
        if isinstance(value, float):
            raise ValueError("floating point prohibited")
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError("non-string key")
                check(child)
        elif isinstance(value, list):
            for child in value:
                check(child)
    try:
        check(payload)
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, OverflowError, RecursionError):
        return {**base, "blocks": ["NONCANONICAL_EVIDENCE"]}
    if type(receipt.get("payload_bytes")) is not int or receipt["payload_bytes"] != len(raw):
        return {**base, "blocks": ["RECEIPT_BYTE_LENGTH_MISMATCH"]}
    actual = hashlib.sha256(raw).hexdigest()
    if actual != receipt["payload_sha256"]:
        return {**base, "blocks": ["RECEIPT_SHA256_MISMATCH"]}
    if receipt.get("record_roles") != list(ROLES):
        return {**base, "blocks": ["RECEIPT_ROLES_MISMATCH"]}
    return {**base, "status": "LOCAL_INTEGRITY_VERIFIED",
            "receipt_verified": True, "payload_sha256": actual,
            "blocks": ["EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED"],
            "verification_scope": "local canonical payload bytes only; external source not verified"}
