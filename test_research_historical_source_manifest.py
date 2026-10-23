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


    def test_publication_after_retrieval_rejected(self):
        record = manifest()
        record["published_at"] = "2026-10-24T10:00:00+00:00"
        with self.assertRaisesRegex(ValueError, "publication_after_retrieval"):
            audit_historical_source_manifest(record, PAYLOAD)

    def test_naive_publication_time_rejected(self):
        record = manifest()
        record["published_at"] = "2026-10-22T10:00:00"
        with self.assertRaisesRegex(ValueError, "publication_timezone_required"):
            audit_historical_source_manifest(record, PAYLOAD)

    def test_valid_publication_time_is_not_proof_of_authenticity(self):
        record = manifest()
        record["published_at"] = "2026-10-22T10:00:00+00:00"
        result = audit_historical_source_manifest(record, PAYLOAD)
        self.assertTrue(result["publication_time_structurally_valid"])
        self.assertFalse(result["publication_time_authenticity_verified"])
        self.assertFalse(result["point_in_time_verified"])


    def test_publication_and_retrieval_compared_as_instants(self):
        record = manifest()
        # 12:00+02:00 equals the 10:00+00:00 retrieval instant.
        record["published_at"] = "2026-10-23T12:00:00+02:00"
        result = audit_historical_source_manifest(record, PAYLOAD)
        self.assertTrue(result["publication_time_structurally_valid"])
        self.assertFalse(result["publication_time_authenticity_verified"])
        # 12:01+02:00 is one minute after retrieval, despite the same date.
        record["published_at"] = "2026-10-23T12:01:00+02:00"
        with self.assertRaisesRegex(ValueError, "publication_after_retrieval"):
            audit_historical_source_manifest(record, PAYLOAD)

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
