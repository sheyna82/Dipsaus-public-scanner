"""External anchoring readiness audit, research-only and fail-closed.

This checks an anchoring plan and receipt metadata; it does NOT fetch receipts,
verify signatures, or independently establish timestamp/source authenticity.
"""
from datetime import datetime, timezone
import re

def _time(s):
    if not isinstance(s, str):
        return None
    try:
        d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return d.astimezone(timezone.utc) if d.tzinfo else None
    except (ValueError, OverflowError):
        return None

def assess_anchor_evidence(chain_head_sha256, receipt):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    if not isinstance(chain_head_sha256, str) or not re.fullmatch(r"[0-9a-f]{64}", chain_head_sha256):
        return {**base, "blocks": ["CHAIN_HEAD_INVALID"]}
    if not isinstance(receipt, dict):
        return {**base, "blocks": ["RECEIPT_MISSING"]}
    required = ("pinned_sha256", "submitted_utc", "receipt_utc", "provider_id",
                "receipt_id", "independent_verification")
    if any(k not in receipt for k in required):
        return {**base, "blocks": ["RECEIPT_FIELDS_MISSING"]}
    if receipt["pinned_sha256"] != chain_head_sha256:
        return {**base, "blocks": ["PIN_MISMATCH"]}
    submitted, received = _time(receipt["submitted_utc"]), _time(receipt["receipt_utc"])
    if submitted is None or received is None or received < submitted:
        return {**base, "blocks": ["RECEIPT_TIME_INVALID"]}
    if any(not isinstance(receipt[k], str) or not receipt[k].strip()
           for k in ("provider_id", "receipt_id")):
        return {**base, "blocks": ["PROVIDER_OR_RECEIPT_ID_MISSING"]}
    # This is a claim in caller-supplied data, not cryptographic verification.
    if receipt["independent_verification"] is not True:
        return {**base, "blocks": ["INDEPENDENT_VERIFICATION_MISSING"]}
    return {**base, "status": "RECEIPT_METADATA_CONSISTENT_ONLY",
            "blocks": ["RECEIPT_SIGNATURE_NOT_VERIFIED",
                       "PROVIDER_INDEPENDENCE_NOT_VERIFIED",
                       "SOURCE_OBSERVATION_TIME_NOT_ATTESTED"],
            "limitations": ["No provider network access or signature verification",
                            "Receipt metadata cannot establish historic price provenance",
                            "Private records must stay in private storage"]}
