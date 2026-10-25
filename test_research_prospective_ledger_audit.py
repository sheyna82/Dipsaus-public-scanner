import json
import tempfile
import unittest
from pathlib import Path
from research_prospective_ledger_audit import audit_prospective_ledger


class ProspectiveAuditTests(unittest.TestCase):
    def test_linkage_pending_and_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / "candidates", root / "outcomes"
            a.mkdir()
            b.mkdir()
            candidate = {"protocol_id": "v1", "symbol": "AMD",
                         "signal_session": "2026-10-26",
                         "future_outcome": None, "trade_ready": False}
            raw = json.dumps(candidate).encode()
            (a / "candidate.json").write_bytes(raw)
            first = audit_prospective_ledger(a, b)
            self.assertTrue(first["integrity_pass"])
            self.assertEqual(first["pending_outcome_count"], 1)
            import hashlib
            outcome = {"protocol_id": "v1", "symbol": "AMD",
                       "signal_session": "2026-10-26",
                       "candidate_sha256": hashlib.sha256(raw).hexdigest(),
                       "trade_ready": False}
            (b / "outcome.json").write_text(json.dumps(outcome))
            self.assertTrue(audit_prospective_ledger(a, b)["integrity_pass"])
            (a / "candidate.json").write_text(json.dumps({**candidate, "changed": True}))
            result = audit_prospective_ledger(a, b)
            self.assertFalse(result["integrity_pass"])
            self.assertEqual(result["errors"][0]["type"], "candidate_hash_mismatch")

    def test_orphan_outcome(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "c", Path(tmp) / "o"
            a.mkdir()
            b.mkdir()
            (b / "orphan.json").write_text(json.dumps({
                "protocol_id": "v1", "symbol": "META", "signal_session": "2026-10-26",
                "candidate_sha256": "invalid", "trade_ready": False}))
            self.assertEqual(audit_prospective_ledger(a, b)["errors"][0]["type"],
                             "orphan_outcome")


if __name__ == "__main__":
    unittest.main()
