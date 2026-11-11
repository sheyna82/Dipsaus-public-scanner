"""Research-only simulated GitHub artifact transport roundtrip.

The outer ZIP models a GitHub Actions artifact download. It is not a real
GitHub API request or independent provenance evidence.
"""
import hashlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from zipfile import ZipFile

from research_immutable_candidate_registration import register_candidate_once
from research_registration_archive_bridge import (
    inspect_candidate_archive, reconcile_verified_archive_summaries)


def inner_archive(candidate_path):
    raw = Path(candidate_path).read_bytes()
    member = "candidates/" + Path(candidate_path).name
    manifest = {"format_version": 1, "research_only": True, "trade_ready": False,
                "files": [{"path": member, "sha256": hashlib.sha256(raw).hexdigest(),
                           "bytes": len(raw)}]}
    stream = io.BytesIO()
    with ZipFile(stream, "w") as z:
        z.writestr(member, raw)
        z.writestr("manifest.json", json.dumps(manifest))
    return stream.getvalue()


def simulated_download(outer_bytes, destination, expected_inner_sha256):
    if len(outer_bytes) > 2_000_000:
        raise ValueError("transport_size_limit")
    with ZipFile(io.BytesIO(outer_bytes)) as z:
        if z.namelist() != ["prospective-ledger-synthetic.zip"]:
            raise ValueError("unexpected_transport_members")
        member = z.getinfo("prospective-ledger-synthetic.zip")
        if member.file_size > 2_000_000:
            raise ValueError("transport_size_limit")
        inner = z.read(member)
    if hashlib.sha256(inner).hexdigest() != expected_inner_sha256:
        raise ValueError("transport_sha256_mismatch")
    with Path(destination).open("xb") as out:
        out.write(inner)
    return inspect_candidate_archive(destination)


class SyntheticTransportIntegrationTests(unittest.TestCase):
    def test_registration_transport_archive_reconciliation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = {"symbol": "AMD", "signal_session": "2026-11-02",
                         "protocol_id": "v1", "future_outcome": None, "trade_ready": False}
            registered = register_candidate_once(candidate, root,
                clock=lambda: datetime(2026, 11, 3, 15, tzinfo=timezone.utc))
            inner = inner_archive(registered["path"])
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", inner)
            summary = simulated_download(outer.getvalue(), root / "restored.zip",
                                         hashlib.sha256(inner).hexdigest())
            self.assertEqual(summary["candidate_count"], 1)
            combined = reconcile_verified_archive_summaries([summary])
            self.assertEqual(combined["candidate_count"], 1)
            self.assertFalse(combined["external_provenance_authenticated"])

    def test_transport_digest_mismatch_fails_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer = io.BytesIO()
            with ZipFile(outer, "w") as z:
                z.writestr("prospective-ledger-synthetic.zip", b"tampered")
            destination = Path(tmp) / "restored.zip"
            with self.assertRaisesRegex(ValueError, "transport_sha256_mismatch"):
                simulated_download(outer.getvalue(), destination, "0" * 64)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
