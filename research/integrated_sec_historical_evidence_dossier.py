"""Research-only historical SEC evidence dossier; fail closed on unverifiable claims.

This dossier intentionally cannot promote internally consistent supplied bytes
to independently authenticated, point-in-time-public trading evidence.
"""
import hashlib
import json
from integrated_sec_complete_submission_audit import inspect_sec_complete_submission


def build_sec_historical_evidence_dossier(candidate_id, raw_bytes, source_url, entry_at):
    if not isinstance(candidate_id, str) or not candidate_id.strip():
        raise ValueError("INVALID_CANDIDATE_ID")
    if len(candidate_id) > 160 or candidate_id != candidate_id.strip():
        raise ValueError("INVALID_CANDIDATE_ID")
    audit = inspect_sec_complete_submission(raw_bytes, source_url, entry_at)
    dossier = {
        "schema": "sec_historical_evidence_dossier_v1",
        "candidate_id": candidate_id,
        "entry_at_claimed": entry_at,
        "sec_audit": audit,
        "evidence_class": "SUPPLIED_BYTES_INTERNAL_CONSISTENCY_ONLY",
        "independent_source_retrieval": False,
        "historical_publication_proven": False,
        "historical_authenticity_independently_proven": False,
        "eligible_for_backtest_performance_claim": False,
        "eligible_for_live_trading_decision": False,
        "missing_evidence": [
            "independently retrieved original SEC source bytes and retrieval receipt",
            "independently timestamped proof of public availability before entry",
            "immutable linkage to historical candidate registration",
        ],
    }
    canonical = json.dumps(dossier, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return {
        "dossier": dossier,
        "dossier_sha256": hashlib.sha256(canonical.encode("ascii")).hexdigest(),
    }


def verify_sec_historical_evidence_dossier(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {"dossier", "dossier_sha256"}:
        raise ValueError("INVALID_SEC_DOSSIER_BUNDLE")
    dossier = bundle["dossier"]
    if not isinstance(dossier, dict) or dossier.get("schema") != "sec_historical_evidence_dossier_v1":
        raise ValueError("INVALID_SEC_DOSSIER_SCHEMA")
    canonical = json.dumps(dossier, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    digest = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    if bundle["dossier_sha256"] != digest:
        raise ValueError("SEC_DOSSIER_HASH_MISMATCH")
    if (dossier.get("evidence_class") != "SUPPLIED_BYTES_INTERNAL_CONSISTENCY_ONLY"
            or dossier.get("independent_source_retrieval") is not False
            or dossier.get("historical_publication_proven") is not False
            or dossier.get("historical_authenticity_independently_proven") is not False
            or dossier.get("eligible_for_backtest_performance_claim") is not False
            or dossier.get("eligible_for_live_trading_decision") is not False):
        raise ValueError("SEC_DOSSIER_UNSUPPORTED_EVIDENCE_PROMOTION")
    audit = dossier.get("sec_audit")
    if (not isinstance(audit, dict)
            or audit.get("source_bytes_authenticity_independently_proven") is not False
            or audit.get("public_dissemination_time_independently_proven") is not False
            or audit.get("trade_ready") is not False
            or audit.get("eligible_for_performance_claim") is not False):
        raise ValueError("SEC_DOSSIER_UNSUPPORTED_AUDIT_PROMOTION")
    return True
