"""Validate the immutable research manifest without activating research."""
import json
import pathlib
import unittest

MANIFEST = pathlib.Path(__file__).with_name("integrated_evidence_manifest.json")
EXPECTED_DIGEST = "27bc6a2bf6e80b4df41faaee53726622f23f1ab495ffcd412639548d025536ee"

class ManifestTests(unittest.TestCase):
    def test_manifest_fails_closed_until_protocol_import(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["schema"], "dipsaus.research_evidence_manifest.v1")
        self.assertTrue(data["research_only"])
        self.assertFalse(data["trade_ready"])
        self.assertFalse(data["protocol_embedded"])
        self.assertEqual(data["validation_state"], "BLOCKED_PENDING_PROTOCOL_IMPORT_AND_CI")

    def test_frozen_source_identity(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["protocol_sha256_canonical_json"], EXPECTED_DIGEST)
        self.assertEqual(data["source_snapshot_commit"], "d953bb21ca68accf6ecbec1a4960feb9b9b3338d")
        self.assertEqual(data["historical_candidates"], 916)
        self.assertEqual(data["selected_candidates"], 96)
        self.assertEqual(data["training_threshold_sets"], 41)

if __name__ == "__main__":
    unittest.main()
