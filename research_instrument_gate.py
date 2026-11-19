"""Research-only instrument identity and venue verification gate.

A valid ISIN checksum does NOT establish listing, market segment,
active trading status, DEGIRO route, fees or quote provenance.
"""
import re

BLOCKED = {"trade_ready": False, "order_placement_enabled": False}


def isin_checksum_valid(isin):
    if not isinstance(isin, str) or re.fullmatch(r"[A-Z]{2}[A-Z0-9]{9}[0-9]", isin) is None:
        return False
    digits = "".join(str(ord(c) - 55) if c.isalpha() else c for c in isin)
    total = 0
    for index, char in enumerate(reversed(digits)):
        value = int(char)
        if index % 2:
            value *= 2
        total += value // 10 + value % 10
    return total % 10 == 0


def assess_instrument(evidence):
    """Require independently attested identity, venue and broker route.

    Flags are assertions from upstream and cannot authenticate sources.
    """
    if not isinstance(evidence, dict):
        return {**BLOCKED, "status": "INSTRUMENT_BLOCKED", "reason": "INVALID_EVIDENCE"}
    isin = evidence.get("isin")
    if not isin_checksum_valid(isin):
        return {**BLOCKED, "status": "INSTRUMENT_BLOCKED", "reason": "INVALID_ISIN"}
    mic = evidence.get("operating_mic")
    if not isinstance(mic, str) or re.fullmatch(r"[A-Z0-9]{4}", mic) is None:
        return {**BLOCKED, "status": "INSTRUMENT_BLOCKED", "reason": "INVALID_MIC"}
    required = ("isin_source_verified", "mic_source_verified",
                "instrument_active_verified", "segment_verified",
                "broker_route_verified", "broker_fee_verified")
    missing = [field for field in required if evidence.get(field) is None]
    if missing:
        return {**BLOCKED, "status": "INSTRUMENT_BLOCKED",
                "reason": "MISSING_VERIFICATION", "missing": missing}
    unverified = [field for field in required if evidence[field] is not True]
    if unverified:
        return {**BLOCKED, "status": "INSTRUMENT_BLOCKED",
                "reason": "UNVERIFIED", "unverified": unverified}
    return {**BLOCKED, "status": "INSTRUMENT_RESEARCH_REVIEW",
            "isin": isin, "operating_mic": mic,
            "source_authenticity_independently_verified": False,
            "note": "Upstream claims only; no independent source attestation or order authorization."}
