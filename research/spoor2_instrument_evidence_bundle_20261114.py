"""Offline orchestration: reconcile ISIN/MIC only after checking evidence bytes.

Supplied source labels, bytes and digests are caller assertions; this never
authenticates a publisher, verifies exchange listing, or enables orders.
"""
from research.spoor2_instrument_artifact_byte_integrity_20261114 import verify_evidence_artifact_bytes
from research.spoor2_instrument_evidence_reconciliation_20261114 import reconcile_instrument_evidence


def inspect_instrument_evidence_bundle(isin, mic, records=()):
    result = {
        "status": "BLOCKED", "byte_integrity_checked": False,
        "reported_cross_source_agreement": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(records, (tuple, list)) or not records:
        result["blocks"].append("EVIDENCE_RECORDS_REQUIRED")
        return result
    metadata = []
    for record in records:
        if not isinstance(record, dict):
            result["blocks"].append("INVALID_EVIDENCE_RECORD")
            return result
        check = verify_evidence_artifact_bytes(
            record.get("artifact_bytes"), record.get("artifact_sha256"),
            record.get("artifact_size"),
        )
        if not check["artifact_bytes_match_declaration"]:
            result["blocks"].extend(check["blocks"])
            return result
        metadata.append({key: record.get(key) for key in
                         ("source_id", "isin", "mic", "artifact_sha256")})
    result["byte_integrity_checked"] = True
    reconciliation = reconcile_instrument_evidence(isin, mic, tuple(metadata))
    if not reconciliation["independent_agreement"]:
        result["blocks"].extend(reconciliation["blocks"])
        return result
    result["reported_cross_source_agreement"] = True
    result["blocks"].append("MATCHING_BYTES_AND_REPORTED_SOURCES_NOT_AUTHORITY")
    return result
