"""Regression tests for cross-run provenance of real downloaded synthetic evidence.

Synthetic evidence records are not registered stock candidates and must never
be counted as such. This module deliberately tests the metadata boundary.
"""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from research_prospective_archive import verify_archive


def audit_synthetic_evidence_pair(archive_a, archive_b):
    records = []
    for path in (archive_a, archive_b):
        verify_archive(path)
        with ZipFile(path) as z:
            record = json.loads(z.read("candidates/synthetic.json"))
        if (record.get("synthetic_data_only") is not True or
                record.get("research_only") is not True or
                record.get("trade_ready") is not False or
                record.get("future_outcome") is not None):
            raise ValueError("not_safe_synthetic_evidence")
        run = record.get("github_run_id_claimed")
        if not isinstance(run, str) or not run.isdecimal() or int(run) <= 0:
            raise ValueError("invalid_claimed_run_id")
        checkout = record.get("workflow_checkout_sha_claimed",
                              record.get("head_sha_claimed"))
        if not isinstance(checkout, str) or len(checkout) != 40 or any(
                c not in "0123456789abcdef" for c in checkout):
            raise ValueError("invalid_claimed_checkout_sha")
        records.append((run, checkout))
    if records[0][0] == records[1][0]:
        raise ValueError("duplicate_claimed_run_id")
    return {"status": "two_synthetic_archives_internally_consistent",
            "claimed_run_ids": [x[0] for x in records],
            "registered_stock_candidates": 0,
            "run_identity_authenticated_externally": False,
            "research_only": True, "trade_ready": False}


class SyntheticEvidencePairTests(unittest.TestCase):
    def make_archive(self, path, run_id, field="workflow_checkout_sha_claimed"):
        record = {"synthetic_data_only": True, "research_only": True,
                  "trade_ready": False, "future_outcome": None,
                  "github_run_id_claimed": run_id, field: "a" * 40}
        import hashlib
        from zipfile import ZipFile
        raw = json.dumps(record).encode()
        member = "candidates/synthetic.json"
        manifest = {"research_only": True, "trade_ready": False,
                    "format_version": 1, "files": [
                        {"path": member, "sha256": hashlib.sha256(raw).hexdigest(),
                         "bytes": len(raw)}]}
        with ZipFile(path, "w") as z:
            z.writestr(member, raw)
            z.writestr("manifest.json", json.dumps(manifest))

    def test_two_distinct_runs_are_not_stock_candidates(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            self.make_archive(a, "101", "head_sha_claimed")
            self.make_archive(b, "102")
            result = audit_synthetic_evidence_pair(a, b)
            self.assertEqual(result["registered_stock_candidates"], 0)
            self.assertFalse(result["run_identity_authenticated_externally"])

    def test_same_run_id_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            self.make_archive(a, "101")
            self.make_archive(b, "101")
            with self.assertRaisesRegex(ValueError, "duplicate_claimed_run_id"):
                audit_synthetic_evidence_pair(a, b)


if __name__ == "__main__":
    unittest.main()
