"""Offline archival package for captured SEC candidate evidence.

The original bytes must be retained separately; this manifest alone cannot
reconstruct them. This package does not prove historical public availability.
"""
import hashlib
import json
from integrated_sec_candidate_capture import capture_sec_candidate


def archive_sec_capture(candidate_id, source_url, entry_at, user_agent, fetcher):
    captured = capture_sec_candidate(candidate_id, source_url, entry_at, user_agent, fetcher)
    receipt = captured["retrieval_receipt"]
    dossier = captured["evidence_dossier"]
    manifest = {
        "schema": "sec_candidate_archive_manifest_v1",
        "candidate_id": candidate_id,
        "source_url": source_url,
        "raw_bytes_sha256": receipt["sha256"],
        "raw_bytes_length": receipt["byte_count"],
        "retrieved_at_utc": receipt["retrieved_at_utc"],
        "dossier_sha256": dossier["dossier_sha256"],
        "historical_publication_independently_proven": False,
        "eligible_for_backtest_performance_claim": False,
        "trade_ready": False,
    }
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {"manifest": manifest, "manifest_sha256": digest, "capture": captured}


def verify_sec_archive(package, raw_bytes):
    if type(raw_bytes) is not bytes or not isinstance(package, dict):
        raise ValueError("INVALID_SEC_ARCHIVE")
    manifest = package.get("manifest")
    captured = package.get("capture")
    if not isinstance(manifest, dict) or not isinstance(captured, dict):
        raise ValueError("INVALID_SEC_ARCHIVE")
    digest = hashlib.sha256(json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if digest != package.get("manifest_sha256"):
        raise ValueError("SEC_ARCHIVE_MANIFEST_HASH_MISMATCH")
    receipt = captured.get("retrieval_receipt")
    dossier = captured.get("evidence_dossier")
    if not isinstance(receipt, dict) or not isinstance(dossier, dict):
        raise ValueError("INVALID_SEC_ARCHIVE")
    from integrated_sec_historical_evidence_dossier import verify_sec_historical_evidence_dossier
    if not verify_sec_historical_evidence_dossier(dossier):
        raise ValueError("SEC_ARCHIVE_DOSSIER_INVALID")
    if (manifest.get("schema") != "sec_candidate_archive_manifest_v1"
            or manifest.get("raw_bytes_sha256") != hashlib.sha256(raw_bytes).hexdigest()
            or manifest.get("raw_bytes_length") != len(raw_bytes)
            or manifest.get("raw_bytes_sha256") != receipt.get("sha256")
            or manifest.get("raw_bytes_length") != receipt.get("byte_count")
            or manifest.get("retrieved_at_utc") != receipt.get("retrieved_at_utc")
            or manifest.get("source_url") != receipt.get("source_url")
            or manifest.get("dossier_sha256") != dossier.get("dossier_sha256")
            or manifest.get("candidate_id") != dossier.get("dossier", {}).get("candidate_id")
            or manifest.get("historical_publication_independently_proven") is not False
            or manifest.get("eligible_for_backtest_performance_claim") is not False
            or manifest.get("trade_ready") is not False):
        raise ValueError("SEC_ARCHIVE_BINDING_MISMATCH")
    return True
