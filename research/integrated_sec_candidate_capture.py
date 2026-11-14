"""Research-only SEC source capture pipeline.

Actual network retrieval is opt-in through an injected callable. A receipt
establishes only capture-time bytes, never pre-entry publication.
"""
import hashlib
from integrated_sec_live_source_retrieval import retrieve_sec_complete_submission
from integrated_sec_historical_evidence_dossier import (
    build_sec_historical_evidence_dossier,
    verify_sec_historical_evidence_dossier,
)


def capture_sec_candidate(candidate_id, source_url, entry_at, user_agent,
                          fetcher=retrieve_sec_complete_submission):
    if not callable(fetcher):
        raise ValueError("INVALID_SEC_FETCHER")
    raw, receipt = fetcher(source_url, user_agent)
    if not isinstance(receipt, dict):
        raise ValueError("INVALID_SEC_RETRIEVAL_RECEIPT")
    if (receipt.get("schema") != "sec_live_retrieval_receipt_v1"
            or receipt.get("source_url") != source_url
            or receipt.get("sha256") != hashlib.sha256(raw).hexdigest()
            or receipt.get("byte_count") != len(raw)
            or receipt.get("historical_publication_independently_proven") is not False
            or receipt.get("eligible_for_performance_claim") is not False
            or receipt.get("trade_ready") is not False):
        raise ValueError("SEC_RETRIEVAL_RECEIPT_MISMATCH")
    dossier = build_sec_historical_evidence_dossier(
        candidate_id, raw, source_url, entry_at,
        retrieved_at=receipt["retrieved_at_utc"])
    if not verify_sec_historical_evidence_dossier(dossier):
        raise ValueError("SEC_DOSSIER_VERIFICATION_FAILED")
    return {
        "schema": "sec_candidate_capture_v1",
        "retrieval_receipt": receipt,
        "evidence_dossier": dossier,
        "historical_publication_independently_proven": False,
        "eligible_for_backtest_performance_claim": False,
        "trade_ready": False,
    }
