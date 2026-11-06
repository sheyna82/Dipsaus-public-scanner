"""Research-only selection from independently hash-checked registration source bytes."""
import hashlib
import json
from integrated_historical_source_bytes_gate import verify_sources
from integrated_verified_priority_selection import compare_verified
from integrated_publication_receipt_audit import audit_publication_receipts

def compare_hash_checked(registrations, source_bytes_by_hash, candidates,
                         capital_eur=50000, max_positions=6, same_day_cash_reuse=True,
                         publication_receipts=None):
    evidence = verify_sources(registrations, source_bytes_by_hash)
    receipt_audit = (audit_publication_receipts(registrations, publication_receipts)
                     if publication_receipts is not None else None)
    selection = compare_verified(registrations, candidates, capital_eur=capital_eur,
                                 max_positions=max_positions, same_day_cash_reuse=same_day_cash_reuse)
    if len(evidence["source_bytes_verified"]) != len(candidates):
        raise ValueError("HASH_CHECKED_COVERAGE_MISMATCH")
    result = {"status": "RESEARCH_ONLY_HASH_CHECKED_PRIORITY_SELECTION",
            "trade_ready": False, "historical_authenticity_independently_proven": False,
            "hash_checked_count": len(evidence["source_bytes_verified"]),
            "research_manifest": {
                "schema": "hash_checked_selection_manifest_v2",
                "input_sha256": selection["selection"]["input_sha256"],
                "fingerprint_schema": selection["selection"]["fingerprint_schema"],
                "capital_eur": selection["selection"]["capital_eur"],
                "max_positions": selection["selection"]["max_positions"],
                "cash_policy": selection["selection"]["cash_policy"],
                "source_sha256": sorted(set(row["source_sha256"] for row in registrations)),
                "registration_evidence": sorted(({
                    "id": row["id"], "source_sha256": row["source_sha256"],
                    "source_available_at_claimed": row["source_available_at"],
                    "registered_at_claimed": row["registered_at"],
                    "entry_at": row["entry_at"]} for row in registrations),
                    key=lambda row: str(row["id"])),
                "external_publication_time_independently_proven": False,
                "source_provenance_status": "CLAIMED_TIMESTAMPS_NOT_INDEPENDENTLY_VERIFIED",
                "eligible_for_performance_claim": False,
                "source_bytes_hash_checked": True,
                "publication_receipt_audit": receipt_audit,
                "publication_receipts_supplied": publication_receipts is not None,
                "historical_authenticity_independently_proven": False,
                "trade_ready": False},
            "selection": selection["selection"],
            "limitations": ["source publication timestamps require independent validation",
                            "hash matching does not prove immutable historical registration"]}

    manifest = result["research_manifest"]
    canonical = json.dumps(manifest, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=True, allow_nan=False).encode("utf-8")
    manifest["manifest_sha256"] = hashlib.sha256(canonical).hexdigest()
    return result

def verify_manifest_fingerprint(manifest):
    """Recompute the research manifest fingerprint; never attest source authenticity."""
    if not isinstance(manifest, dict) or manifest.get("schema") != "hash_checked_selection_manifest_v2":
        raise ValueError("INVALID_MANIFEST_SCHEMA")
    digest = manifest.get("manifest_sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("INVALID_MANIFEST_FINGERPRINT")
    payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
    try:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("INVALID_MANIFEST_CONTENT") from exc
    if hashlib.sha256(canonical).hexdigest() != digest:
        raise ValueError("MANIFEST_FINGERPRINT_MISMATCH")
    for key in ("trade_ready", "historical_authenticity_independently_proven",
                "external_publication_time_independently_proven", "eligible_for_performance_claim"):
        if manifest.get(key) is not False:
            raise ValueError("UNSUPPORTED_EVIDENCE_PROMOTION")
    audit = manifest.get("publication_receipt_audit")
    if audit is None:
        if manifest.get("publication_receipts_supplied") is not False:
            raise ValueError("RECEIPT_AUDIT_COVERAGE_MISMATCH")
    else:
        if manifest.get("publication_receipts_supplied") is not True or not isinstance(audit, dict):
            raise ValueError("RECEIPT_AUDIT_COVERAGE_MISMATCH")
        if audit.get("audit_fingerprint_schema") != "publication_receipt_audit_v2":
            raise ValueError("INVALID_RECEIPT_AUDIT_SCHEMA")
        receipts = audit.get("receipts")
        if not isinstance(receipts, list) or audit.get("receipt_count") != len(receipts):
            raise ValueError("RECEIPT_AUDIT_COVERAGE_MISMATCH")
        canonical_receipts = json.dumps(sorted(receipts, key=lambda row: str(row["id"])),
                                        sort_keys=True, separators=(",", ":"),
                                        ensure_ascii=True, allow_nan=False).encode("utf-8")
        if hashlib.sha256(canonical_receipts).hexdigest() != audit.get("audit_sha256"):
            raise ValueError("RECEIPT_AUDIT_FINGERPRINT_MISMATCH")
        registrations = manifest.get("registration_evidence")
        if not isinstance(registrations, list) or len(registrations) != len(receipts):
            raise ValueError("RECEIPT_REGISTRATION_BINDING_MISMATCH")
        expected = {str(row["id"]): row for row in registrations}
        if len(expected) != len(registrations):
            raise ValueError("RECEIPT_REGISTRATION_BINDING_MISMATCH")
        for receipt in receipts:
            ident = str(receipt["id"])
            row = expected.get(ident)
            if row is None or any((
                    receipt.get("source_sha256") != row.get("source_sha256"),
                    receipt.get("source_available_at_claimed") != row.get("source_available_at_claimed"),
                    receipt.get("registered_at_claimed") != row.get("registered_at_claimed"),
                    receipt.get("entry_at") != row.get("entry_at"))):
                raise ValueError("RECEIPT_REGISTRATION_BINDING_MISMATCH")
        if audit.get("external_publication_time_independently_proven") is not False or (
                audit.get("eligible_for_performance_claim") is not False) or (
                audit.get("trade_ready") is not False):
            raise ValueError("UNSUPPORTED_EVIDENCE_PROMOTION")
    return {"fingerprint_verified": True, "trade_ready": False,
            "historical_authenticity_independently_proven": False}
