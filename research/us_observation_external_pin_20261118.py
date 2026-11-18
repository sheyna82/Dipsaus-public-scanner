"""Offline externally pinned chain-head verification.

An independently retained expected head digest can detect full-chain rewrite.
This function NEVER asserts that the external pin is authentic or timestamped.
"""
import re
from research.us_observation_chain_20261118 import verify_chain

def verify_pinned_head(chain, pin):
    base = {"status": "BLOCKED", "trade_ready": False, "notify": False,
            "automatic_orders": False, "order_placement_enabled": False,
            "research_only": True}
    check = verify_chain(chain)
    if check["status"] != "VALID":
        return {**base, "blocks": ["CHAIN_INVALID"]}
    if not isinstance(pin, dict):
        return {**base, "blocks": ["EXTERNAL_PIN_MISSING"]}
    expected = pin.get("expected_head_sha256")
    count = pin.get("expected_count")
    reference = pin.get("external_reference")
    if (not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or type(count) is not int or count < 1
            or not isinstance(reference, str) or not reference.strip()):
        return {**base, "blocks": ["EXTERNAL_PIN_INVALID"]}
    if count != check["count"] or expected != check["head_hash"]:
        return {**base, "blocks": ["EXTERNAL_PIN_MISMATCH"]}
    return {**base, "status": "CONSISTENT_WITH_SUPPLIED_PIN",
            "blocks": ["PIN_INDEPENDENCE_NOT_ATTESTED",
                       "PIN_TIMESTAMP_NOT_ATTESTED",
                       "SOURCE_AUTHENTICITY_NOT_ATTESTED"],
            "verified_count": count,
            "limitations": ["Pin supplied by caller, not fetched or independently authenticated",
                            "Consistency does not establish observation time or source validity"]}
