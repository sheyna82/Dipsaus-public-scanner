"""Research-only source evidence archive bound to an immutable candidate record.

Stores the exact source bytes alongside the registered candidate in a separate
ZIP. Neither the source content nor its timestamp is independently authenticated.
"""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED


def archive_source_evidence(candidate_path, source_bytes, destination):
    if not isinstance(source_bytes, bytes) or not source_bytes:
        raise ValueError("missing_source_bytes")
    if len(source_bytes) > 5_000_000:
        raise ValueError("source_snapshot_too_large")
    candidate_path = Path(candidate_path)
    record_bytes = candidate_path.read_bytes()
    record = json.loads(record_bytes)
    digest = hashlib.sha256(source_bytes).hexdigest()
    if record.get("source_snapshot_sha256") != digest or record.get("source_snapshot_bytes") != len(source_bytes):
        raise ValueError("source_candidate_binding_mismatch")
    if record.get("trade_ready") is not False or record.get("research_only") is not True or record.get("future_outcome") is not None:
        raise ValueError("unsafe_candidate")
    identity = record.get("candidate_identity_sha256")
    if not isinstance(identity, str) or len(identity) != 64 or any(c not in "0123456789abcdef" for c in identity):
        raise ValueError("invalid_candidate_identity")
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError("source_archive_already_exists")
    manifest = {
        "format_version": 1, "research_only": True, "trade_ready": False,
        "independent_source_authentication": False,
        "candidate_identity_sha256": identity,
        "candidate_sha256": hashlib.sha256(record_bytes).hexdigest(),
        "source_sha256": digest, "source_bytes": len(source_bytes),
    }
    with ZipFile(destination, "x", compression=ZIP_DEFLATED) as z:
        z.writestr("candidate.json", record_bytes)
        z.writestr("source.bin", source_bytes)
        z.writestr("manifest.json", json.dumps(manifest, sort_keys=True) + "\n")
    return verify_source_evidence_archive(destination)


def verify_source_evidence_archive(path):
    with ZipFile(path) as z:
        infos = z.infolist()
        if len(infos) != 3 or {i.filename for i in infos} != {"candidate.json", "source.bin", "manifest.json"}:
            raise ValueError("invalid_source_archive_members")
        if any(i.file_size > 5_000_000 for i in infos):
            raise ValueError("source_archive_member_too_large")
        manifest = json.loads(z.read("manifest.json"))
        candidate_raw = z.read("candidate.json")
        source_raw = z.read("source.bin")
    candidate = json.loads(candidate_raw)
    if manifest.get("format_version") != 1 or manifest.get("research_only") is not True or manifest.get("trade_ready") is not False or manifest.get("independent_source_authentication") is not False:
        raise ValueError("unsafe_source_manifest")
    if candidate.get("trade_ready") is not False or candidate.get("research_only") is not True or candidate.get("future_outcome") is not None:
        raise ValueError("unsafe_candidate")
    if not source_raw or hashlib.sha256(source_raw).hexdigest() != manifest.get("source_sha256") or len(source_raw) != manifest.get("source_bytes"):
        raise ValueError("source_archive_digest_mismatch")
    if hashlib.sha256(candidate_raw).hexdigest() != manifest.get("candidate_sha256"):
        raise ValueError("candidate_archive_digest_mismatch")
    if candidate.get("source_snapshot_sha256") != manifest["source_sha256"] or candidate.get("source_snapshot_bytes") != len(source_raw) or candidate.get("candidate_identity_sha256") != manifest.get("candidate_identity_sha256"):
        raise ValueError("source_candidate_binding_mismatch")
    return {
        "status": "source_bytes_and_candidate_locally_verified",
        "source_sha256": manifest["source_sha256"],
        "candidate_sha256": manifest["candidate_sha256"],
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "trade_ready": False,
    }
