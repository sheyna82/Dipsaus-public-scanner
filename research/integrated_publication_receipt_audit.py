"""Fail-closed audit of externally supplied publication receipts; no authenticity promotion."""
import hashlib
import json
from urllib.parse import urlsplit
from integrated_historical_priority_provenance import _timestamp

def audit_publication_receipts(registrations, receipts):
    if not isinstance(registrations, list) or not isinstance(receipts, list):
        raise ValueError("INVALID_RECEIPT_INPUT")
    expected = {str(row["id"]): row for row in registrations}
    if len(expected) != len(registrations):
        raise ValueError("DUPLICATE_REGISTRATION")
    seen = set()
    checked = []
    for receipt in receipts:
        if not isinstance(receipt, dict):
            raise ValueError("INVALID_RECEIPT")
        ident = str(receipt.get("id", ""))
        if ident in seen:
            raise ValueError("DUPLICATE_RECEIPT")
        seen.add(ident)
        if ident not in expected:
            raise ValueError("UNKNOWN_RECEIPT_ID")
        raw = receipt.get("raw_bytes")
        if type(raw) is not bytes:
            raise ValueError("RECEIPT_BYTES_MISSING")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != receipt.get("receipt_sha256"):
            raise ValueError("RECEIPT_HASH_MISMATCH")
        if receipt.get("source_sha256") != expected[ident].get("source_sha256"):
            raise ValueError("RECEIPT_SOURCE_BINDING_MISMATCH")
        observed = _timestamp(receipt.get("observed_at"))
        registered = _timestamp(expected[ident]["registered_at"])
        entry = _timestamp(expected[ident]["entry_at"])
        available = _timestamp(expected[ident]["source_available_at"])
        if observed < available:
            raise ValueError("RECEIPT_BEFORE_CLAIMED_SOURCE_AVAILABILITY")
        if observed > registered or observed >= entry:
            raise ValueError("RECEIPT_TOO_LATE")
        url = receipt.get("source_url")
        if not isinstance(url, str):
            raise ValueError("INVALID_RECEIPT_URL")
        try:
            parsed = urlsplit(url)
            valid_url = (parsed.scheme == "https" and bool(parsed.hostname)
                         and not parsed.username and not parsed.password
                         and not any(ch.isspace() for ch in url))
        except ValueError:
            valid_url = False
        if not valid_url:
            raise ValueError("INVALID_RECEIPT_URL")
        checked.append({"id": ident, "receipt_sha256": digest,
                        "source_sha256": receipt["source_sha256"],
                        "observed_at_claimed": receipt["observed_at"],
                        "source_url_claimed": receipt["source_url"],
                        "receipt_bytes_hash_checked": True,
                        "independent_publication_time_proven": False})
    if seen != set(expected):
        raise ValueError("RECEIPT_COVERAGE_MISMATCH")
    canonical = json.dumps(sorted(checked, key=lambda x: x["id"]), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    audit_sha256 = hashlib.sha256(canonical).hexdigest()
    return {"status": "RESEARCH_ONLY_RECEIPT_AUDIT",
            "audit_sha256": audit_sha256, "audit_fingerprint_schema": "publication_receipt_audit_v1",
            "receipt_count": len(checked), "receipts": sorted(checked, key=lambda x: x["id"]),
            "external_publication_time_independently_proven": False,
            "evidence_level": "SUPPLIED_RECEIPT_BYTES_ONLY",
            "independent_verification_requirements": [
                "independently retrieve publisher or trusted archive record",
                "verify publisher or archive identity and source content",
                "verify externally attested publication or capture timestamp",
                "bind independently verified timestamp to the pre-entry registration"],
            "eligible_for_performance_claim": False, "trade_ready": False,
            "limitations": ["receipt timestamps and URLs are supplied claims",
                            "independent archive or publisher verification remains required"]}
