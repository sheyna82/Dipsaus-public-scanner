"""Synthetic checks for event market provenance; no fetched market data."""
import unittest
from research_event_market_provenance import audit_market_observation


def sample(**changes):
    record = dict(symbol="AMD", observation_timestamp_utc="2026-10-23T20:00:00Z",
                  retrieved_at_utc="2026-10-24T08:00:00Z",
                  source_url="https://example.org/fixture",
                  content_sha256="a" * 64, exchange="XNYS", currency="USD")
    record.update(changes)
    return audit_market_observation(record, "2026-10-24T12:00:00Z")


class MarketProvenanceTests(unittest.TestCase):
    def test_envelope_is_not_independent_verification(self):
        result = sample()
        self.assertTrue(result["provenance_envelope_valid"])
        self.assertFalse(result["digest_recomputed_against_source"])
        self.assertFalse(result["source_authenticity_verified"])
        self.assertFalse(result["trade_ready"])

    def test_no_retroactive_retrieval_or_future_observation(self):
        for change in (
            {"retrieved_at_utc": "2026-10-25T08:00:00Z"},
            {"observation_timestamp_utc": "2026-10-24T09:00:00Z",
             "retrieved_at_utc": "2026-10-24T08:00:00Z"},
        ):
            with self.subTest(change=change):
                with self.assertRaisesRegex(ValueError, "provenance_temporal_order_invalid"):
                    sample(**change)

    def test_digest_url_and_timezone_validation(self):
        with self.assertRaisesRegex(ValueError, "invalid_content_digest"):
            sample(content_sha256="placeholder")
        with self.assertRaisesRegex(ValueError, "source_must_be_https"):
            sample(source_url="http://example.org")
        with self.assertRaisesRegex(ValueError, "provenance_timezone_required"):
            sample(retrieved_at_utc="2026-10-24T08:00:00")


if __name__ == "__main__":
    unittest.main()
