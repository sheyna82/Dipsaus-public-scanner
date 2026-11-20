import unittest
from research_batch_fingerprint import fingerprint_batch as fingerprint

MANIFEST = {"batch_id": "synthetic", "started_utc": "2026-01-01T00:00:00Z",
            "completed_utc": "2026-01-01T01:00:00Z",
            "expected_signal_count": 2,
            "expected_decision_counts": {"SELECTED": 1, "REJECTED": 1, "DEFERRED": 0}}
def signal(i, decision):
    return {"schema_version": 1, "event_id": format(i, "032x"),
            "candidate_id": format(i + 100, "032x"),
            "observed_utc": "2026-01-01T00:30:00Z",
            "event_type": "SIGNAL", "source_digest": "a" * 64,
            "feature_digest": "b" * 64, "decision": decision}
EVENTS = [signal(1, "SELECTED"), signal(2, "REJECTED")]

class BatchFingerprintTests(unittest.TestCase):
    def test_order_independent(self):
        a = fingerprint(MANIFEST, EVENTS)
        b = fingerprint(MANIFEST, list(reversed(EVENTS)))
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertFalse(a["archive_integrity_independently_verified"])

    def test_matching_reference_is_not_independent_attestation(self):
        digest = fingerprint(MANIFEST, EVENTS)["sha256"]
        r = fingerprint(MANIFEST, EVENTS, expected_digest=digest)
        self.assertTrue(r["matches_expected_digest"])
        self.assertFalse(r["external_reference_attested"])

    def test_changed_signal_detected_against_reference(self):
        digest = fingerprint(MANIFEST, EVENTS)["sha256"]
        changed = [EVENTS[0], {**EVENTS[1], "source_digest": "c" * 64}]
        self.assertFalse(fingerprint(MANIFEST, changed, expected_digest=digest)
                         ["matches_expected_digest"])

    def test_missing_signal_blocks_fingerprint(self):
        self.assertEqual(fingerprint(MANIFEST, EVENTS[:1])["status"],
                         "BATCH_FINGERPRINT_BLOCKED")

    def test_invalid_expected_digest_blocks(self):
        self.assertEqual(fingerprint(MANIFEST, EVENTS, expected_digest="bad")["reason"],
                         "INVALID_EXPECTED_DIGEST")

    def test_extra_private_field_blocks(self):
        self.assertEqual(fingerprint(MANIFEST, [{**EVENTS[0], "ticker": "private"},
                                                EVENTS[1]])["status"],
                         "BATCH_FINGERPRINT_BLOCKED")

if __name__ == "__main__":
    unittest.main()
