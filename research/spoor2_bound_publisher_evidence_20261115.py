"""Offline publisher-metadata and artifact-byte binding, without source attestation.

All inputs are caller supplied. Matching metadata to verified bytes only prevents
internal mismatches; it cannot establish official publisher identity or freshness.
"""
import hashlib
import hmac

from research.spoor2_instrument_artifact_byte_integrity_20261114 import (
    verify_evidence_artifact_bytes,
)
from research.spoor2_instrument_publisher_provenance_20261115 import (
    inspect_publisher_provenance,
)


def inspect_bound_publisher_evidence(record):
    result = {
        "status": "BLOCKED", "artifact_bytes_match_declaration": False,
        "publisher_metadata_well_formed": False, "metadata_bound_to_artifact": False,
        "publisher_identity_verified": False, "retrieval_freshness_verified": False,
        "independent_source_authority_verified": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(record, dict):
        result["blocks"].append("BOUND_EVIDENCE_RECORD_REQUIRED")
        return result
    byte_check = verify_evidence_artifact_bytes(
        record.get("artifact_bytes"), record.get("artifact_sha256"),
        record.get("artifact_size"),
    )
    if not byte_check["artifact_bytes_match_declaration"]:
        result["blocks"].extend(byte_check["blocks"])
        return result
    result["artifact_bytes_match_declaration"] = True
    provenance = record.get("publisher_provenance")
    provenance_check = inspect_publisher_provenance(provenance)
    if not provenance_check["publisher_metadata_well_formed"]:
        result["blocks"].extend(provenance_check["blocks"])
        return result
    result["publisher_metadata_well_formed"] = True
    # Require the metadata's claimed identity and artifact declaration to match
    # this very record, not an unrelated file or another source label.
    source = record.get("source_id")
    if (not isinstance(source, str) or not source
            or provenance.get("publisher_id") != source):
        result["blocks"].append("PUBLISHER_SOURCE_BINDING_MISMATCH")
        return result
    declared_hash = provenance.get("artifact_sha256")
    declared_size = provenance.get("artifact_size")
    if (not isinstance(declared_hash, str) or len(declared_hash) != 64
            or any(c not in "0123456789abcdefABCDEF" for c in declared_hash)
            or not isinstance(declared_size, int) or isinstance(declared_size, bool)
            or declared_size <= 0):
        result["blocks"].append("PUBLISHER_ARTIFACT_BINDING_REQUIRED")
        return result
    if (declared_size != byte_check["byte_count"]
            or not hmac.compare_digest(
                declared_hash.lower(),
                hashlib.sha256(record["artifact_bytes"]).hexdigest(),
            )):
        result["blocks"].append("PUBLISHER_ARTIFACT_BINDING_MISMATCH")
        return result
    result["metadata_bound_to_artifact"] = True
    result["blocks"].append("CALLER_SUPPLIED_BINDING_NOT_OFFICIAL_PUBLISHER_ATTESTATION")
    return result
