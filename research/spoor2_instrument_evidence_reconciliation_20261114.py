"""Offline cross-source ISIN/MIC evidence reconciliation, never trade admission.

Inputs are explicit evidence records, not a network fetch or official authority
claim. Conflicts and missing independent sources remain BLOCKED.
"""
from research.spoor2_instrument_reference_gate_20261114 import inspect_instrument_reference


def reconcile_instrument_evidence(isin, mic, records=()):
    result = {
        "status": "BLOCKED", "independent_agreement": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    syntax = inspect_instrument_reference(isin, mic)
    if not syntax["identifier_syntax_valid"]:
        result["blocks"].extend(syntax["blocks"])
        return result
    if not isinstance(records, (tuple, list)) or not records:
        result["blocks"].append("EVIDENCE_RECORDS_REQUIRED")
        return result
    source_pairs = {}
    source_hashes = {}
    for record in records:
        if not isinstance(record, dict):
            result["blocks"].append("INVALID_EVIDENCE_RECORD")
            return result
        source = record.get("source_id")
        record_isin = record.get("isin")
        record_mic = record.get("mic")
        evidence_sha = record.get("artifact_sha256")
        if (not isinstance(source, str) or not source.strip() or source != source.strip()
                or not isinstance(evidence_sha, str) or len(evidence_sha) != 64
                or any(c not in "0123456789abcdefABCDEF" for c in evidence_sha)
                or not isinstance(record_isin, str)
                or not isinstance(record_mic, str)):
            result["blocks"].append("INCOMPLETE_EVIDENCE_PROVENANCE")
            return result
        if not inspect_instrument_reference(record_isin, record_mic)["identifier_syntax_valid"]:
            result["blocks"].append("INVALID_EVIDENCE_IDENTIFIER")
            return result
        pair = (record_isin, record_mic)
        if source in source_pairs and source_pairs[source] != pair:
            result["blocks"].append("INTRA_SOURCE_CONFLICT")
            return result
        source_pairs[source] = pair
        if source in source_hashes and source_hashes[source] != evidence_sha.lower():
            result["blocks"].append("INTRA_SOURCE_ARTIFACT_CONFLICT")
            return result
        source_hashes[source] = evidence_sha.lower()
    if len(source_pairs) < 2:
        result["blocks"].append("TWO_DISTINCT_SOURCES_REQUIRED")
        return result
    if len(set(source_hashes.values())) < 2:
        result["blocks"].append("DISTINCT_ARTIFACT_HASHES_REQUIRED")
        return result
    if set(source_pairs.values()) != {(isin, mic)}:
        result["blocks"].append("CROSS_SOURCE_INSTRUMENT_CONFLICT")
        return result
    result["independent_agreement"] = True
    result["source_count"] = len(source_pairs)
    result["blocks"].append("REPORTED_AGREEMENT_NOT_INDEPENDENTLY_ATTESTED")
    return result
