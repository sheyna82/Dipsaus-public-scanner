"""Offline historical price dataset gate regression tests."""
import hashlib
import unittest

from research_historical_price_ingest_gate import audit_historical_price_dataset

PAYLOAD = b"date,open,high,low,close,volume\n2026-01-02,10,12,9,11,100\n"


def manifest(payload=PAYLOAD):
    return {
        "provider": "synthetic fixture",
        "dataset": "synthetic daily bars",
        "source_url": "https://example.org/fixture",
        "license_reference": "test-only synthetic data",
        "retrieved_at": "2026-10-23T10:00:00+00:00",
        "sha256": hashlib.sha256(payload).hexdigest(),
        "adjustment_policy": "unadjusted",
        "universe_policy": "single synthetic symbol",
    }


class HistoricalPriceIngestTests(unittest.TestCase):
    def test_both_gates_pass_without_provenance_claim(self):
        result = audit_historical_price_dataset(manifest(), PAYLOAD)
        self.assertTrue(result["accepted"])
        self.assertTrue(result["manifest_consistent"])
        self.assertTrue(result["ohlcv_structure_valid"])
        self.assertFalse(result["provider_authenticity_verified"])
        self.assertFalse(result["license_verified"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["research_data_ready"])
        self.assertTrue(result["requires_external_license_review"])
        self.assertTrue(result["requires_external_provenance_review"])
        self.assertTrue(result["requires_point_in_time_reconstruction"])
        for check in ("corporate_actions_verified",
                      "delisted_symbols_coverage_verified",
                      "survivorship_bias_control_verified",
                      "benchmark_independence_verified"):
            with self.subTest(check=check):
                self.assertFalse(result[check])
        for check in ("requires_corporate_action_review",
                      "requires_delisting_coverage_review",
                      "requires_survivorship_bias_review",
                      "requires_independent_benchmark_review"):
            with self.subTest(check=check):
                self.assertTrue(result[check])


    def test_long_calendar_gap_is_reported_not_misclassified(self):
        payload = (b"date,open,high,low,close,volume\\n"
                   b"2026-01-02,10,12,9,11,100\\n"
                   b"2026-01-20,11,13,10,12,110\\n")
        # Gap size is descriptive: holidays, halts, and missing bars
        # require an independently checked exchange session calendar.
        payload = payload.replace(b"\\\\n", b"\\n")
        result = audit_historical_price_dataset(manifest(payload), payload)
        self.assertEqual(result["largest_calendar_gap_days"], 18)
        self.assertEqual(result["gaps_over_seven_days"], 1)
        self.assertFalse(result["exchange_session_completeness_verified"])
        self.assertTrue(result["requires_exchange_session_completeness_review"])

    def test_changed_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "payload_hash_mismatch"):
            audit_historical_price_dataset(manifest(), PAYLOAD + b"\n")

    def test_valid_hash_cannot_hide_bad_prices(self):
        invalid = b"date,open,high,low,close,volume\n2026-01-02,10,8,9,11,100\n"
        with self.assertRaisesRegex(ValueError, "invalid_ohlcv"):
            audit_historical_price_dataset(manifest(invalid), invalid)


if __name__ == "__main__":
    unittest.main()
