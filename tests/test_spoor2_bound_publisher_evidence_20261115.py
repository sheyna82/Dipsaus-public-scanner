"""Synthetic offline tests for publisher-to-artifact declaration binding."""
import hashlib
import unittest

from research.spoor2_bound_publisher_evidence_20261115 import (
    inspect_bound_publisher_evidence,
)


def record():
    data = b"synthetic-publisher-data"
    digest = hashlib.sha256(data).hexdigest()
    return {
        "source_id": "synthetic-publisher",
        "artifact_bytes": data,
        "artifact_sha256": digest,
        "artifact_size": len(data),
        "publisher_provenance": {
            "publisher_id": "synthetic-publisher",
            "retrieval_url": "https://example.org/file.csv",
            "retrieved_at_utc": "2026-11-15T12:00:00+00:00",
            "artifact_sha256": digest,
            "artifact_size": len(data),
        },
    }


class BoundPublisherEvidenceTests(unittest.TestCase):
    def test_matching_declarations_do_not_attest_publisher(self):
        r = inspect_bound_publisher_evidence(record())
        self.assertTrue(r["artifact_bytes_match_declaration"])
        self.assertTrue(r["publisher_metadata_well_formed"])
        self.assertTrue(r["metadata_bound_to_artifact"])
        self.assertEqual(r["status"], "BLOCKED")
        for key in ("publisher_identity_verified", "retrieval_freshness_verified",
                    "independent_source_authority_verified", "source_attested",
                    "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[key])

    def test_caller_cannot_override_safety_flags(self):
        v = record()
        v.update({
            "source_attested": True,
            "trade_ready": True,
            "order_placement_enabled": True,
        })
        v["publisher_provenance"].update({
            "publisher_identity_verified": True,
            "retrieval_freshness_verified": True,
            "independent_source_authority_verified": True,
        })
        r = inspect_bound_publisher_evidence(v)
        self.assertTrue(r["metadata_bound_to_artifact"])
        for key in ("publisher_identity_verified", "retrieval_freshness_verified",
                    "independent_source_authority_verified", "source_attested",
                    "instrument_segment_verified", "broker_route_verified",
                    "trade_ready", "order_placement_enabled"):
            self.assertFalse(r[key])

    def test_source_mismatch_blocks(self):
        v = record()
        v["publisher_provenance"]["publisher_id"] = "other"
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["PUBLISHER_SOURCE_BINDING_MISMATCH"])
        self.assertFalse(r["metadata_bound_to_artifact"])

    def test_digest_mismatch_blocks(self):
        v = record()
        v["publisher_provenance"]["artifact_sha256"] = "0" * 64
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["PUBLISHER_ARTIFACT_BINDING_MISMATCH"])

    def test_size_mismatch_blocks(self):
        v = record()
        v["publisher_provenance"]["artifact_size"] += 1
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["PUBLISHER_ARTIFACT_BINDING_MISMATCH"])

    def test_missing_binding_blocks(self):
        v = record()
        del v["publisher_provenance"]["artifact_sha256"]
        self.assertEqual(inspect_bound_publisher_evidence(v)["blocks"],
                         ["PUBLISHER_ARTIFACT_BINDING_REQUIRED"])

    def test_modified_bytes_block_before_metadata(self):
        v = record()
        v["artifact_bytes"] += b"tampered"
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["ARTIFACT_BYTE_COUNT_MISMATCH"])
        self.assertFalse(r["publisher_metadata_well_formed"])

    def test_invalid_provenance_blocks(self):
        v = record()
        v["publisher_provenance"]["retrieval_url"] = "http://example.org/file.csv"
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["INVALID_RETRIEVAL_URL"])

    def test_boolean_artifact_size_not_accepted(self):
        v = record()
        v["publisher_provenance"]["artifact_size"] = True
        r = inspect_bound_publisher_evidence(v)
        self.assertEqual(r["blocks"], ["PUBLISHER_ARTIFACT_BINDING_REQUIRED"])


if __name__ == "__main__":
    unittest.main()
