"""Read-only verifier for downloaded synthetic provider evidence.

Checks transport package, candidate/source manifest and the provider bar.
No independent authenticity or prospective timing claim is made.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
from zipfile import ZipFile

from research_alpha_vantage_offline_daily import inspect_alpha_vantage_daily_bytes
from research_source_evidence_archive import verify_source_evidence_archive
import tempfile


def verify_downloaded_provider_artifact(outer_bytes):
    if not isinstance(outer_bytes, bytes) or not outer_bytes or len(outer_bytes) > 10_000_000:
        raise ValueError("invalid_artifact_bytes")
    with ZipFile(io.BytesIO(outer_bytes)) as outer:
        names = outer.namelist()
        if len(names) != 2 or set(names) != {"synthetic-provider-evidence.zip", "sha256.txt"}:
            raise ValueError("unexpected_artifact_members")
        if any(info.file_size > (5_000_000 if info.filename.endswith(".zip") else 512) for info in outer.infolist()):
            raise ValueError("oversized_artifact_member")
        inner_bytes = outer.read("synthetic-provider-evidence.zip")
        checksum = outer.read("sha256.txt").decode("ascii")
    expected_line = hashlib.sha256(inner_bytes).hexdigest() + "  synthetic-provider-evidence.zip\n"
    if checksum != expected_line:
        raise ValueError("artifact_checksum_mismatch")
    with ZipFile(io.BytesIO(inner_bytes)) as inner:
        names = inner.namelist()
        if len(names) != 3 or set(names) != {"candidate.json", "source.bin", "manifest.json"}:
            raise ValueError("unexpected_evidence_members")
        if any(info.file_size > 5_000_000 for info in inner.infolist()):
            raise ValueError("oversized_evidence_member")
        candidate_raw = inner.read("candidate.json")
        source_raw = inner.read("source.bin")
        manifest = json.loads(inner.read("manifest.json"))
    with tempfile.TemporaryDirectory() as tmp:
        evidence_path = Path(tmp) / "evidence.zip"
        evidence_path.write_bytes(inner_bytes)
        verify_source_evidence_archive(evidence_path)
    candidate = json.loads(candidate_raw)
    if (manifest.get("candidate_sha256") != hashlib.sha256(candidate_raw).hexdigest()
            or manifest.get("source_sha256") != hashlib.sha256(source_raw).hexdigest()
            or candidate.get("source_snapshot_sha256") != manifest.get("source_sha256")):
        raise ValueError("evidence_digest_mismatch")
    if (candidate.get("synthetic_data_only") is not True
            or candidate.get("provider_format") != "alpha_vantage_daily"
            or candidate.get("research_only") is not True
            or candidate.get("trade_ready") is not False
            or candidate.get("prospective_signal_proven") is not False
            or candidate.get("bar_available_at_observation_time_verified") is not False):
        raise ValueError("unsafe_or_unexpected_candidate")
    checked = inspect_alpha_vantage_daily_bytes(
        source_raw, expected_symbol=candidate["symbol"],
        as_of_session=candidate["signal_session"])
    if checked["bar"] != candidate.get("provider_bar"):
        raise ValueError("provider_bar_binding_mismatch")
    return {
        "status": "downloaded_synthetic_provider_evidence_verified",
        "candidate_sha256": manifest["candidate_sha256"],
        "source_sha256": manifest["source_sha256"],
        "synthetic_data_only": True,
        "independent_source_authentication": False,
        "independent_timestamp_proof": False,
        "trade_ready": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-zip", required=True, type=Path)
    args = parser.parse_args(argv)
    result = verify_downloaded_provider_artifact(args.artifact_zip.read_bytes())
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
