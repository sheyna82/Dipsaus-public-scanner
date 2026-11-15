"""Synthetic publisher provenance tests; no network or source authority."""
import unittest

from research.spoor2_instrument_publisher_provenance_20261115 import inspect_publisher_provenance


def record(**overrides):
    value = {
        "publisher_id": "synthetic-publisher",
        "retrieval_url": "https://example.org/reference.csv",
        "retrieved_at_utc": "2026-11-15T12:00:00+00:00",
    }
    value.update(overrides)
    return value


class PublisherProvenanceTests(unittest.TestCase):
    def test_valid_metadata_does_not_attest_source(self):
        result = inspect_publisher_provenance(record(
            publisher_identity_verified=True, source_attested=True, trade_ready=True))
        self.assertTrue(result["publisher_metadata_well_formed"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["blocks"], ["PUBLISHER_IDENTITY_NOT_INDEPENDENTLY_VERIFIED"])
        for flag in ("publisher_identity_verified", "independent_source_authority_verified",
                     "source_attested", "trade_ready", "order_placement_enabled"):
            self.assertFalse(result[flag])

    def test_missing_record_blocks(self):
        self.assertEqual(inspect_publisher_provenance(None)["blocks"],
                         ["PUBLISHER_PROVENANCE_REQUIRED"])

    def test_untrusted_url_forms_block(self):
        for url in ("http://example.org/a", "https://user@example.org/a",
                    "https://example.org/a#fragment", "https://example.org:8443/a",
                    "https://example.org./a", "https://example.org/a\n"):
            with self.subTest(url=url):
                result = inspect_publisher_provenance(record(retrieval_url=url))
                self.assertEqual(result["blocks"], ["INVALID_RETRIEVAL_URL"])
                self.assertFalse(result["source_attested"])

    def test_missing_or_non_utc_timestamp_blocks(self):
        for value in (None, "", "2026-11-15T12:00:00", "2026-11-15T13:00:00+01:00"):
            with self.subTest(value=value):
                self.assertEqual(
                    inspect_publisher_provenance(record(retrieved_at_utc=value))["blocks"],
                    ["INVALID_RETRIEVAL_TIMESTAMP"])

    def test_invalid_publisher_label_blocks(self):
        for value in ("", " publisher ", None, "x" * 129):
            with self.subTest(value=value):
                self.assertEqual(
                    inspect_publisher_provenance(record(publisher_id=value))["blocks"],
                    ["INVALID_PUBLISHER_ID"])


if __name__ == "__main__":
    unittest.main()
