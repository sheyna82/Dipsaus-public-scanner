"""Verify actual two-file synthetic GitHub artifact transport, read-only.

The outer GitHub artifact ZIP contains an inner ledger ZIP and sha256.txt.
This checks both and does not treat synthetic data as stock candidates.
"""
import hashlib
import io
import re
from zipfile import ZipFile, BadZipFile

from research_prospective_archive import verify_archive


def verify_synthetic_artifact_transport(outer_bytes, inner_destination, *, max_bytes=8_000_000):
    if not isinstance(outer_bytes, bytes) or len(outer_bytes) > max_bytes:
        raise ValueError("invalid_outer_payload")
    try:
        with ZipFile(io.BytesIO(outer_bytes)) as outer:
            names = outer.namelist()
            expected = {"prospective-ledger-synthetic.zip", "sha256.txt"}
            if len(names) != 2 or set(names) != expected:
                raise ValueError("unexpected_artifact_members")
            if any(outer.getinfo(name).file_size > max_bytes for name in names):
                raise ValueError("artifact_member_too_large")
            inner = outer.read("prospective-ledger-synthetic.zip")
            checksum = outer.read("sha256.txt")
    except BadZipFile as exc:
        raise ValueError("invalid_artifact_zip") from exc
    if len(inner) > max_bytes or len(checksum) > 200:
        raise ValueError("artifact_member_too_large")
    line = checksum.decode("ascii")
    match = re.fullmatch(r"([0-9a-f]{64})  prospective-ledger-synthetic\.zip\n", line)
    if match is None or hashlib.sha256(inner).hexdigest() != match.group(1):
        raise ValueError("inner_archive_checksum_mismatch")
    from pathlib import Path
    destination = Path(inner_destination)
    with destination.open("xb") as out:
        out.write(inner)
    try:
        result = verify_archive(destination)
    except Exception:
        destination.unlink()
        raise
    return {"status": "synthetic_transport_verified",
            "inner_sha256": match.group(1),
            "inner_manifest_verified": result["valid"],
            "synthetic_data_only": True,
            "registered_stock_candidates": 0,
            "external_github_artifact_digest_verified": False,
            "trade_ready": False}
