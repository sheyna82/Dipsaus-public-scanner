"""Regression tests for historical dataset source manifest integrity."""
import hashlib
import unittest

from research_historical_source_manifest import audit_historical_source_manifest


PAYLOAD = b"date,close\n2018-09-04,10.0\n"


def manifest():
    return {
        "provider": "fixture only",
        "dataset": "test prices",
        "source_url": "https://example.org/fixture",
        "license_reference": "fixture; not real market data",
        "retrieved_at": "2026-10-23T10:00:00+00:00",
        "sha256": hashlib.sha256(PAYLOAD).hexdigest(),
        "adjustment_policy": "unadjusted",
        "universe_policy": "test fixture only",
    }


class SourceManifestTests(unittest.TestCase):
    def test_matching_payload_is_not_authenticated(self):
        result = audit_historical_source_manifest(manifest(), PAYLOAD)
        self.assertTrue(result["manifest_consistent"])
        self.assertFalse(result["provider_authenticity_verified"])
        self.assertFalse(result["license_verified"])
        self.assertFalse(result["point_in_time_verified"])
        self.assertFalse(result["trade_ready"])

    def test_modified_payload_rejected(self):
        with self.assertRaisesRegex(ValueError, "payload_hash_mismatch"):
            audit_historical_source_manifest(manifest(), PAYLOAD + b"tamper")

    def test_missing_license_reference_rejected(self):
        record = manifest()
        del record["license_reference"]
        with self.assertRaisesRegex(ValueError, "incomplete_manifest"):
            audit_historical_source_manifest(record, PAYLOAD)

    def test_naive_retrieval_timestamp_rejected(self):
        record = manifest()
        record["retrieved_at"] = "2026-10-23T10:00:00"
        with self.assertRaisesRegex(ValueError, "timezone_required"):
            audit_historical_source_manifest(record, PAYLOAD)


if __name__ == "__main__":
    unittest.main()
