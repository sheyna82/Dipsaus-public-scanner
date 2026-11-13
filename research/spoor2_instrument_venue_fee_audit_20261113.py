"""Offline, fail-closed instrument/venue/DEGIRO fee evidence audit.

This module never fetches data, authorizes a trade or estimates a fee.
Identifiers, exchange listings and broker tariffs require separate primary
source records with independent provenance. Research-only.
"""
import re

_ISIN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", re.ASCII)
_MIC = re.compile(r"^[A-Z0-9]{4}$", re.ASCII)
_FIELDS = ("symbol", "isin", "venue_mic", "market")


def isin_checksum_valid(value):
    """ISO 6166 format + mod-10 checksum; not registration evidence."""
    if not isinstance(value, str) or not _ISIN.fullmatch(value):
        return False
    expanded = "".join(str(ord(c) - 55) if "A" <= c <= "Z" else c for c in value)
    total = 0
    for index, digit in enumerate(reversed(expanded)):
        number = int(digit) * (2 if index % 2 else 1)
        total += number // 10 + number % 10
    return total % 10 == 0


def audit_instrument_venue_fee(candidate, isin_record=None, mic_record=None,
                               listing_record=None, degiro_record=None):
    """Reject unsupported assertions; evidence records are never self-authorizing.

    Every record must be a dict with independent_verification=True, a
    nonempty source_url, retrieved_utc and source_version. These are
    documentary completeness checks, NOT cryptographic source attestation.
    In particular independent_verification is a claimant-supplied flag.
    """
    blocks = []
    result = {
        "status": "BLOCKED", "isin_checksum_valid": False,
        "mic_format_valid": False, "isin_registered": False,
        "mic_registered": False, "listing_verified": False,
        "degiro_fee_verified": False, "source_attested": False,
        "trade_ready": False, "order_placement_enabled": False,
    }
    if not isinstance(candidate, dict) or any(
        not isinstance(candidate.get(k), str) or not candidate[k]
        for k in _FIELDS
    ):
        return {**result, "blocks": ["INVALID_INSTRUMENT_IDENTITY"]}
    isin, mic = candidate["isin"], candidate["venue_mic"]
    result["isin_checksum_valid"] = isin_checksum_valid(isin)
    result["mic_format_valid"] = bool(_MIC.fullmatch(mic))
    if not result["isin_checksum_valid"]:
        blocks.append("ISIN_FORMAT_OR_CHECKSUM_INVALID")
    if not result["mic_format_valid"]:
        blocks.append("MIC_FORMAT_INVALID")

    def evidence_ok(record, kind, required):
        if not isinstance(record, dict):
            blocks.append(kind + "_PRIMARY_EVIDENCE_MISSING")
            return False
        metadata = ("source_url", "retrieved_utc", "source_version")
        if (record.get("independent_verification") is not True
                or any(not isinstance(record.get(k), str) or not record[k]
                       for k in metadata)
                or any(record.get(k) != candidate.get(k) for k in required)):
            blocks.append(kind + "_PRIMARY_EVIDENCE_UNVERIFIED")
            return False
        return True

    # Separate authorities: an ISIN record cannot prove venue listing.
    result["isin_registered"] = (
        result["isin_checksum_valid"]
        and evidence_ok(isin_record, "ISIN", ("isin",)))
    result["mic_registered"] = (
        result["mic_format_valid"]
        and evidence_ok(mic_record, "MIC", ("venue_mic",)))
    result["listing_verified"] = (
        result["isin_registered"] and result["mic_registered"]
        and evidence_ok(listing_record, "LISTING", _FIELDS))
    # A fee must be for the exact broker, instrument, venue, product and
    # currency, not inferred from country, ISIN prefix or MIC alone.
    if result["listing_verified"]:
        fee_fields = _FIELDS + ("product_type", "trading_currency")
        if (not isinstance(candidate.get("product_type"), str)
                or not isinstance(candidate.get("trading_currency"), str)
                or not candidate["product_type"] or not candidate["trading_currency"]):
            blocks.append("DEGIRO_FEE_CLASSIFICATION_MISSING")
        elif (evidence_ok(degiro_record, "DEGIRO_FEE", fee_fields)
              and degiro_record.get("broker") == "DEGIRO"
              and isinstance(degiro_record.get("tariff_effective_date"), str)
              and bool(degiro_record["tariff_effective_date"])
              and isinstance(degiro_record.get("tariff_rule_id"), str)
              and bool(degiro_record["tariff_rule_id"])):
            result["degiro_fee_verified"] = True
        else:
            blocks.append("DEGIRO_TARIFF_AUTHORITY_NOT_ESTABLISHED")
    # No primary source data or broker tariffs are bundled/approved here.
    # Even fully populated claimant-supplied records cannot attest authority.
    blocks.append("INDEPENDENT_SOURCE_AUTHORITY_NOT_ATTESTED")
    blocks.append("DEGIRO_EXECUTION_QUOTE_NOT_VERIFIED")
    return {**result, "blocks": list(dict.fromkeys(blocks))}
