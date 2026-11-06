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
    return {"fingerprint_verified": True, "trade_ready": False,
            "historical_authenticity_independently_proven": False}
