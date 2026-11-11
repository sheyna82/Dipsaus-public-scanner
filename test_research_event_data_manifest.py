"""Synthetic manifest tests; no external evidence is claimed."""
import unittest
from research_event_data_manifest import (
    REQUIRED_ARTIFACTS, build_event_data_manifest)


class EventDataManifestTests(unittest.TestCase):
    def test_six_events_explicitly_lack_real_evidence(self):
        result = build_event_data_manifest()
        self.assertEqual(len(result["records"]), 6)
        self.assertTrue(all(len(r["missing_verified_artifacts"]) ==
                            len(REQUIRED_ARTIFACTS) for r in result["records"]))
        self.assertTrue(all(not r["data_ready"] and not r["trade_ready"]
                            for r in result["records"]))
        self.assertFalse(result["real_data_collected_by_this_module"])

    def test_unverified_labels_do_not_count(self):
        result = build_event_data_manifest({"AMD": {
            "issuer_event_confirmation": {"verified": False},
            "pre_event_stock_prices": {"verified": "yes"},
        }})
        amd = next(r for r in result["records"] if r["symbol"] == "AMD")
        self.assertEqual(amd["verified_artifact_count"], 0)

    def test_invalid_input_rejected(self):
        with self.assertRaisesRegex(ValueError, "artifacts_must_be_mapping"):
            build_event_data_manifest([])
        with self.assertRaisesRegex(ValueError, "symbol_artifacts_must_be_mapping"):
            build_event_data_manifest({"AMD": "claimed"})


if __name__ == "__main__":
    unittest.main()
