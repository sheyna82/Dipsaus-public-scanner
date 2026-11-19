"""Offline instrument-identity consistency contract; not source authentication.

Symbol alone cannot uniquely identify a listing. This checks explicit market,
venue and ISIN assertions in supplied records. No network or trade execution.
"""
import re

_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")


def _valid_isin(value):
    if not isinstance(value, str) or not _ISIN.fullmatch(value):
        return False
    digits = "".join(str(int(char, 36)) if char.isalpha() else char for char in value)
    total = 0
    for index, char in enumerate(reversed(digits)):
        digit = int(char)
        if index % 2:
            digit *= 2
        total += digit // 10 + digit % 10
    return total % 10 == 0


def audit_instrument_identity(candidate):
    base = {"status": "BLOCKED", "trade_ready": False,
            "order_placement_enabled": False}
    if not isinstance(candidate, dict):
        return {**base, "blocks": ["INVALID_CANDIDATE"]}
    symbol, market, venue, isin = (
        candidate.get(key) for key in ("symbol", "market", "venue_mic", "isin"))
    fields = {"symbol": symbol, "market": market, "venue_mic": venue, "isin": isin}
    blocks = []
    for key, value in fields.items():
        if not isinstance(value, str) or not value or value != value.strip():
            blocks.append("INSTRUMENT_" + key.upper() + "_MISSING")
    if isinstance(venue, str) and venue and not re.fullmatch(r"[A-Z0-9]{4}", venue):
        blocks.append("INSTRUMENT_VENUE_MIC_INVALID")
    if isinstance(isin, str) and not _valid_isin(isin):
        blocks.append("INSTRUMENT_ISIN_INVALID")
    for role in ("broker", "invalidation", "resistance"):
        technical = candidate.get("technical_evidence")
        record = technical.get(role + "_evidence") if isinstance(technical, dict) else None
        for key, expected in fields.items():
            observed = record.get(key) if isinstance(record, dict) else None
            if not isinstance(observed, str) or not observed:
                blocks.append(role.upper() + "_" + key.upper() + "_NOT_DECLARED")
            elif observed != expected:
                blocks.append(role.upper() + "_" + key.upper() + "_MISMATCH")
    return {**base,
            "status": "CONSISTENT_CLAIMS_NOT_EXTERNALLY_ATTESTED" if not blocks else "BLOCKED",
            "blocks": list(dict.fromkeys(blocks)) +
                      ["EXTERNAL_INSTRUMENT_ATTESTATION_NOT_CONNECTED"]}
