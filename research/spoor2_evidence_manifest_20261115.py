"""Deterministic, offline inventory of caller-supplied evidence artifacts.

A manifest documents claims and byte checks; it never establishes publisher
identity, independent source authority, exchange listing, or trade readiness.
"""
import hashlib
import json
import unicodedata

from research.spoor2_instrument_artifact_byte_integrity_20261114 import verify_evidence_artifact_bytes


def build_evidence_manifest(records=()):
    result = {
        "status": "BLOCKED", "manifest_complete": False,
        "byte_integrity_checked": False, "records": [],
        "duplicate_source_ids": [], "shared_artifact_hashes": [],
        "manifest_sha256": None, "independent_source_authority_verified": False,
        "source_attested": False, "instrument_segment_verified": False,
        "broker_route_verified": False, "trade_ready": False,
        "order_placement_enabled": False, "blocks": [],
    }
    if not isinstance(records, (tuple, list)) or not records:
        result["blocks"].append("EVIDENCE_RECORDS_REQUIRED")
        return result
    inventory = []
    for record in records:
        if not isinstance(record, dict):
            result["blocks"].append("INVALID_EVIDENCE_RECORD")
            return result
        source = record.get("source_id")
        if (not isinstance(source, str) or not source.strip()
                or source != source.strip() or len(source) > 128
                or any(unicodedata.category(ch) in ("Cc", "Cf") for ch in source)):
            result["blocks"].append("INVALID_SOURCE_ID")
            return result
        check = verify_evidence_artifact_bytes(
            record.get("artifact_bytes"), record.get("artifact_sha256"),
            record.get("artifact_size"))
        if not check["artifact_bytes_match_declaration"]:
            result["blocks"].extend(check["blocks"])
            return result
        inventory.append({
            "source_id": source.casefold(),
            "artifact_sha256": record["artifact_sha256"].lower(),
            "artifact_size": record["artifact_size"],
        })
    inventory.sort(key=lambda r: (r["source_id"], r["artifact_sha256"], r["artifact_size"]))
    sources = {}
    hashes = {}
    for item in inventory:
        sources[item["source_id"]] = sources.get(item["source_id"], 0) + 1
        hashes.setdefault(item["artifact_sha256"], set()).add(item["source_id"])
    result["records"] = inventory
    result["duplicate_source_ids"] = sorted(k for k, n in sources.items() if n > 1)
    result["shared_artifact_hashes"] = sorted(k for k, ids in hashes.items() if len(ids) > 1)
    result["byte_integrity_checked"] = True
    result["manifest_complete"] = True
    canonical = json.dumps(inventory, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    result["manifest_sha256"] = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    if result["duplicate_source_ids"]:
        result["blocks"].append("DUPLICATE_SOURCE_IDENTIFIERS")
    if result["shared_artifact_hashes"]:
        result["blocks"].append("SHARED_ARTIFACT_ACROSS_SOURCE_LABELS")
    result["blocks"].append("CALLER_SUPPLIED_MANIFEST_NOT_INDEPENDENT_ATTESTATION")
    return result
