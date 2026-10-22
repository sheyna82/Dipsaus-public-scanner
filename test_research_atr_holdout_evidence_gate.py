import unittest
from research_atr_holdout_evidence_gate import assess_holdout_readiness


class ATRHoldoutEvidenceGateTests(unittest.TestCase):
    def test_missing_evidence_blocks(self):
        result = assess_holdout_readiness({}, {})
        self.assertEqual(result["status"], "DATA_BLOCKED")
        self.assertFalse(result["trade_ready"])
        self.assertIn("missing_provider_rights_checked", result["errors"])

    def test_attestations_never_claim_independent_verification(self):
        # Synthetic metadata: even a fully checked form is NOT external verification.
        manifest = {"provider": "example", "source_url": "https://example.org/data",
                    "license_name": "example", "license_url": "https://example.org/license",
                    "retrieved_at": "2026-01-01T00:00:00+00:00",
                    "price_adjustment": "raw", "timezone": "UTC",
                    "survivorship_policy": "includes_delisted",
                    "corporate_actions_policy": "verified",
                    "point_in_time_policy": "verified_release_timestamps",
                    "universe_definition": "synthetic"}
        fields = ("provider_rights_checked", "raw_data_sha256_checked",
                  "corporate_actions_independently_verified",
                  "delisted_coverage_verified", "security_identity_asof_verified",
                  "benchmark_sessions_verified", "signal_timestamps_verified",
                  "outcomes_uninspected_before_freeze")
        audit = {field: True for field in fields}
        audit.update({"protocol_frozen_at": "2026-01-01T00:00:00+00:00",
                      "first_holdout_signal_at": "2026-02-01T00:00:00+00:00",
                      "independent_signal_days": 100, "independent_severe_events": 30})
        result = assess_holdout_readiness(manifest, audit)
        self.assertEqual(result["status"], "METADATA_REVIEW_REQUIRED")
        self.assertFalse(result["independent_holdout_verified"])
        self.assertFalse(result["trade_ready"])

    def test_invalid_freeze_order_blocks(self):
        result = assess_holdout_readiness({}, {"protocol_frozen_at": "2026-03-01T00:00:00+00:00",
                                              "first_holdout_signal_at": "2026-02-01T00:00:00+00:00"})
        self.assertIn("invalid_freeze_order", result["errors"])


if __name__ == "__main__":
    unittest.main()
