import hashlib
import unittest

from research_source_snapshot_binding import bind_source_snapshot


class SourceSnapshotBindingTests(unittest.TestCase):
    def setUp(self):
        self.data = b'{"close":123.45,"fixture":true}'
        self.digest = hashlib.sha256(self.data).hexdigest()
        self.observation = {
            "research_only": True, "trade_ready": False,
            "future_outcome": None,
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
        }

    def bind(self):
        return bind_source_snapshot(self.observation, self.data, expected_sha256=self.digest)

    def test_bytes_bound_but_not_authenticated(self):
        result = self.bind()
        self.assertEqual(result["source_snapshot_sha256"], self.digest)
        self.assertEqual(result["source_snapshot_bytes"], len(self.data))
        self.assertFalse(result["independent_source_authentication"])
        self.assertFalse(result["trade_ready"])
        self.assertNotIn("source_snapshot_sha256", self.observation)

    def test_tampered_bytes_rejected(self):
        with self.assertRaisesRegex(ValueError, "source_snapshot_digest_mismatch"):
            bind_source_snapshot(self.observation, self.data + b"x", expected_sha256=self.digest)

    def test_caller_supplied_digest_metadata_rejected(self):
        self.observation["source_snapshot_sha256"] = self.digest
        with self.assertRaisesRegex(ValueError, "caller_supplied_source_snapshot_metadata_forbidden"):
            self.bind()

    def test_authentication_claim_rejected(self):
        self.observation["independent_source_authentication"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_source_authentication_claim"):
            self.bind()

    def test_empty_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing_source_bytes"):
            bind_source_snapshot(self.observation, b"", expected_sha256=self.digest)

    def test_bad_digest_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_expected_sha256"):
            bind_source_snapshot(self.observation, self.data, expected_sha256="not-a-digest")


if __name__ == "__main__":
    unittest.main()
