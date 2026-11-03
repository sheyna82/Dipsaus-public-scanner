"""Research-only bridge from verified archive bytes to registration reconciliation.

Accepts local archive files; downloading and authenticating GitHub provenance
remain separate responsibilities. No extraction or repository writes.
"""
import hashlib
import json
from pathlib import PurePosixPath
from zipfile import ZipFile

from research_candidate_registration_reconciliation import reconcile_candidate_records


def inspect_candidate_archive(archive_path):
    with ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "manifest.json" not in names:
            raise ValueError("invalid_archive_members")
        manifest = json.loads(archive.read("manifest.json"))
        if manifest.get("trade_ready") is not False or manifest.get("format_version") != 1:
            raise ValueError("invalid_archive_manifest")
        entries = manifest.get("files")
        if not isinstance(entries, list):
            raise ValueError("invalid_archive_manifest")
        expected = {"manifest.json"}
        candidates = []
        for entry in entries:
            name = entry["path"]
            parts = PurePosixPath(name).parts
            if len(parts) != 2 or parts[0] not in ("candidates", "outcomes") or not parts[1].endswith(".json"):
                raise ValueError("unsafe_archive_path")
            if name in expected:
                raise ValueError("duplicate_archive_member")
            expected.add(name)
            raw = archive.read(name)
            if len(raw) != entry["bytes"] or hashlib.sha256(raw).hexdigest() != entry["sha256"]:
                raise ValueError("archive_checksum_mismatch")
            if parts[0] == "candidates":
                record = json.loads(raw)
                if record.get("trade_ready") is not False or record.get("future_outcome") is not None:
                    raise ValueError("unsafe_candidate")
                identity = {key: record[key] for key in ("protocol_id", "symbol", "signal_session")}
                identity_digest = hashlib.sha256(json.dumps(
                    identity, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
                if record.get("candidate_identity_sha256") != identity_digest:
                    raise ValueError("candidate_identity_digest_mismatch")
                candidates.append({"identity": identity_digest, "sha256": hashlib.sha256(raw).hexdigest()})
        if set(names) != expected:
            raise ValueError("unexpected_archive_member")
    return {"status": "archive_manifest_verified",
            "candidates": candidates, "candidate_count": len(candidates),
            "external_provenance_authenticated": False,
            "research_only": True, "trade_ready": False}


def reconcile_verified_archive_summaries(summaries):
    identities = {}
    for summary in summaries:
        if summary.get("status") != "archive_manifest_verified":
            raise ValueError("archive_not_verified")
        for item in summary["candidates"]:
            identity, digest = item["identity"], item["sha256"]
            if identity in identities and identities[identity] != digest:
                raise ValueError("cross_archive_candidate_conflict")
            identities[identity] = digest
    return {"status": "known_archives_reconciled",
            "candidate_count": len(identities),
            "all_historical_archives_discovered": False,
            "external_provenance_authenticated": False,
            "research_only": True, "trade_ready": False}
