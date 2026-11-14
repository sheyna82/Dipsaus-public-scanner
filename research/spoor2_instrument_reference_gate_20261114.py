"""Offline ISIN/MIC comparison against explicit, independently reviewed evidence.

No lookup, exchange claim, DEGIRO route or trade permission is inferred.
"""
import re

_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")
_MIC = re.compile(r"^[A-Z0-9]{4}$")


def _isin_checksum_valid(value):
    digits = "".join(str(int(char, 36)) if char.isalpha() else char for char in value)
    total = 0
    for i, char in enumerate(reversed(digits)):
        n = int(char)
        if i % 2:
            n *= 2
        total += n // 10 + n % 10
    return total % 10 == 0


def inspect_instrument_reference(isin, mic, reviewed_pairs=()):
    result = {
        "status": "BLOCKED", "identifier_syntax_valid": False,
        "reviewed_pair_match": False, "source_attested": False,
        "instrument_segment_verified": False, "broker_route_verified": False,
        "trade_ready": False, "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(isin, str) or not _ISIN.fullmatch(isin) or not _isin_checksum_valid(isin):
        result["blocks"].append("INVALID_ISIN")
        return result
    if not isinstance(mic, str) or not _MIC.fullmatch(mic):
        result["blocks"].append("INVALID_MIC")
        return result
    result["identifier_syntax_valid"] = True
    if (not isinstance(reviewed_pairs, (tuple, frozenset))
            or not reviewed_pairs
            or any(not isinstance(p, tuple) or len(p) != 2 for p in reviewed_pairs)):
        result["blocks"].append("INDEPENDENT_REFERENCE_REQUIRED")
        return result
    if (isin, mic) not in reviewed_pairs:
        result["blocks"].append("UNVERIFIED_INSTRUMENT_MARKET_PAIR")
        return result
    result["reviewed_pair_match"] = True
    result["blocks"].append("PAIR_MATCH_NOT_SOURCE_OR_BROKER_ATTESTATION")
    return result
