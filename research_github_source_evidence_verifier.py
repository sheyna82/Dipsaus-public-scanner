"""Verify a downloaded synthetic source-byte GitHub artifact against API metadata.

No market-source authentication, exchange-cutoff proof, or trade authorization.
"""
import hashlib
import io
import re
import tempfile
from pathlib import Path
from zipfile import ZipFile

from research_source_evidence_archive import verify_source_evidence_archive


def verify_github_source_evidence(outer_bytes, metadata, *, expected_run_id, expected_head_sha):
    if not isinstance(metadata, dict) or not isinstance(metadata.get("workflow_run"), dict):
        raise ValueError("invalid_github_metadata")
    if type(expected_run_id) is not int or expected_run_id <= 0:
        raise ValueError("invalid_expected_run")
    if not isinstance(expected_head_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", expected_head_sha):
        raise ValueError("invalid_expected_head")
    if metadata["workflow_run"].get("id") != expected_run_id or metadata["workflow_run"].get("head_sha") != expected_head_sha:
        raise ValueError("github_run_identity_mismatch")
    if metadata.get("name") != "dipsaus-source-bytes-synthetic-evidence" or metadata.get("expired") is not False:
        raise ValueError("unexpected_or_expired_artifact")
    claimed = metadata.get("digest")
    if not isinstance(claimed, str) or not re.fullmatch(r"sha256:[0-9a-f]{64}", claimed):
        raise ValueError("invalid_github_digest")
    if not isinstance(outer_bytes, bytes) or hashlib.sha256(outer_bytes).hexdigest() != claimed[7:]:
        raise ValueError("github_artifact_digest_mismatch")
    with ZipFile(io.BytesIO(outer_bytes)) as outer:
        infos = outer.infolist()
        if len(infos) != 2 or {i.filename for i in infos} != {"source-evidence-synthetic.zip", "sha256.txt"}:
            raise ValueError("unexpected_outer_members")
        if any(i.file_size > 6_000_000 for i in infos):
            raise ValueError("oversized_outer_member")
        inner = outer.read("source-evidence-synthetic.zip")
        checksum_text = outer.read("sha256.txt").decode("ascii")
    digest = hashlib.sha256(inner).hexdigest()
    if checksum_text != digest + "  source-evidence-synthetic.zip\n":
        raise ValueError("inner_archive_digest_mismatch")
    with tempfile.TemporaryDirectory(prefix="dipsaus-source-check-") as directory:
        path = Path(directory) / "inner.zip"
        path.write_bytes(inner)
        checked = verify_source_evidence_archive(path)
        with ZipFile(path) as z:
            import json
            candidate = json.loads(z.read("candidate.json"))
            if candidate.get("synthetic_data_only") is not True:
                raise ValueError("not_synthetic_candidate")
    return {
        **checked,
        "status": "github_synthetic_source_bytes_verified",
        "github_artifact_id": metadata.get("id"),
        "github_run_id": expected_run_id,
        "github_outer_sha256": claimed[7:],
        "inner_archive_sha256": digest,
        "external_github_artifact_digest_verified": True,
        "independent_source_authentication": False,
        "prospective_stock_registration_verified": False,
        "trade_ready": False,
    }
