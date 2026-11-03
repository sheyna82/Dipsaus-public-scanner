import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from research_prospective_core_integration import audit_registered_candidate_entry


class CoreIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "captured_at_utc": "2026-11-03T14:57:22+00:00",
            "last_common_eligible_session": "2026-11-02",
            "prospective_candidate_registered": False,
            "independent_prospective_proof": False,
        }
        self.stock = {"symbol": "AMD", "session": "2026-11-04", "open": "100.5",
                      "retrieved_at_utc": "2026-11-04T21:00:00+00:00",
                      "source_verified_independently": True}
        self.spy = dict(self.stock, symbol="SPY")

    def candidate(self, root, **changes):
        data = {"protocol_id": "v1", "symbol": "AMD",
                "signal_session": "2026-11-02",
                "registered_at_utc": "2026-11-03T15:00:00+00:00",
                "future_outcome": None, "trade_ready": False}
        data.update(changes)
        path = Path(root) / "candidate.json"
        path.write_text(json.dumps(data))
        return path

    def test_bound_candidate_is_still_not_verified(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.candidate(tmp)
            result = audit_registered_candidate_entry(path, self.manifest,
                                                        self.stock, self.spy)
            self.assertEqual(result["candidate_sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest())
            self.assertTrue(result["registration_boundary_passed"])
            self.assertFalse(result["entry_reference_accepted"])
            self.assertFalse(result["outcome_eligible"])
            self.assertFalse(result["trade_ready"])

    def test_candidate_symbol_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "candidate_entry_symbol_mismatch"):
                audit_registered_candidate_entry(
                    self.candidate(tmp, symbol="META"), self.manifest, self.stock, self.spy)

    def test_registration_before_capture_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "candidate_registered_before_source_capture"):
                audit_registered_candidate_entry(
                    self.candidate(tmp, registered_at_utc="2026-11-03T14:00:00+00:00"),
                    self.manifest, self.stock, self.spy)

    def test_signal_after_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "candidate_signal_after_eligible_source"):
                audit_registered_candidate_entry(
                    self.candidate(tmp, signal_session="2026-11-03"),
                    self.manifest, self.stock, self.spy)


if __name__ == "__main__":
    unittest.main()
