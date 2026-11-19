"""Offline reconciliation regression tests using synthetic fixtures only."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from integrated_historical_reconciliation import reconcile, canonical_digest

class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = {"research_only": True, "trade_ready": False, "horizon_sessions": 10,
                     "cost_bps": 50, "portfolio_oos": {
                         "recovery": {"candidate_audit": [
                             {"filter_selected": True}, {"filter_selected": False}]}}}
        self.source_files = {"candidate_feature_oos.json": self.data,
                             "candidate_feature_oos_input_snapshot.json": {"test": 1},
                             "candidate_feature_portfolio_quarters.json": {"test": 2}}
        self.protocol = {"historical_source": {
            "artifact_file_sha256": {},
            "historical_candidate_counts": {"recovery": {"candidate_n": 2, "selected_n": 1}}}}
        self.write_fixture()

    def write_fixture(self):
        for name, value in self.source_files.items():
            raw = json.dumps(value, sort_keys=True).encode()
            (self.root / name).write_bytes(raw)
            self.protocol["historical_source"]["artifact_file_sha256"][name] = hashlib.sha256(raw).hexdigest()
        (self.root / "prospective_filter_protocol_v1_1.json").write_text(json.dumps(self.protocol), encoding="utf-8")
        (self.root / "prospective_filter_protocol_v1_1.sha256").write_text(canonical_digest(self.protocol), encoding="utf-8")

    def test_valid_reconciliation_is_research_only(self):
        result = reconcile(self.root)
        self.assertEqual(result["verified_artifacts"], 3)
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["prospective_validated"])

    def test_tampered_artifact_rejected(self):
        (self.root / "candidate_feature_oos.json").write_text('{"tampered":true}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "SOURCE_ARTIFACT_MISMATCH"):
            reconcile(self.root)

    def test_changed_protocol_rejected(self):
        p = self.root / "prospective_filter_protocol_v1_1.json"
        p.write_text(p.read_text(encoding="utf-8") + " ", encoding="utf-8")
        # Formatting alone must not change canonical JSON digest.
        self.assertFalse(reconcile(self.root)["trade_ready"])
        p.write_text(json.dumps({"historical_source": {}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "PROTOCOL_DIGEST_MISMATCH"):
            reconcile(self.root)

    def test_candidate_count_mismatch_rejected(self):
        self.data["portfolio_oos"]["recovery"]["candidate_audit"].append({"filter_selected": True})
        self.source_files["candidate_feature_oos.json"] = self.data
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "HISTORICAL_CANDIDATE_COUNTS_MISMATCH"):
            reconcile(self.root)

    def test_unsafe_trade_ready_rejected(self):
        self.data["trade_ready"] = True
        self.source_files["candidate_feature_oos.json"] = self.data
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "UNSAFE_HISTORICAL_STATUS"):
            reconcile(self.root)

    def test_path_traversal_rejected(self):
        self.protocol["historical_source"]["artifact_file_sha256"]["../outside.json"] = "0"*64
        self.write_fixture()
        with self.assertRaisesRegex(ValueError, "UNSAFE_ARTIFACT_FILENAME"):
            reconcile(self.root)

if __name__ == "__main__":
    unittest.main()
