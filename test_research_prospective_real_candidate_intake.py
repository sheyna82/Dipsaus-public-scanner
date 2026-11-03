import unittest
from datetime import datetime, timezone

from research_prospective_real_candidate_intake import validate_prospective_observation


class ProspectiveRealIntakeTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 11, 3, 16, tzinfo=timezone.utc)
        self.record = {
            "symbol": "AMD", "protocol_id": "research-v1",
            "signal_session": "2026-11-02",
            "source_name": "example-unverified",
            "source_url": "https://example.org/market/AMD",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "independent_source_authentication": False,
            "independent_timestamp_proof": False,
            "future_outcome": None,
            "research_only": True, "trade_ready": False,
        }

    def validate(self):
        return validate_prospective_observation(self.record, now_utc=self.now)

    def test_schema_acceptance_is_not_market_authentication(self):
        result = self.validate()
        self.assertFalse(result["prospective_signal_proven"])
        self.assertFalse(result["trade_ready"])

    def test_future_source_timestamp_rejected(self):
        self.record["source_observed_at_utc"] = "2026-11-04T15:00:00Z"
        with self.assertRaisesRegex(ValueError, "future_observation"):
            self.validate()

    def test_future_signal_session_rejected(self):
        self.record["signal_session"] = "2026-11-04"
        with self.assertRaisesRegex(ValueError, "future_observation"):
            self.validate()

    def test_future_outcome_rejected(self):
        self.record["future_outcome"] = {"return": 1}
        with self.assertRaisesRegex(ValueError, "future_outcome_forbidden"):
            self.validate()

    def test_authentication_claim_rejected(self):
        self.record["independent_source_authentication"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_source_authentication_claim"):
            self.validate()

    def test_untrusted_timestamp_claim_rejected(self):
        self.record["independent_timestamp_proof"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_timestamp_claim"):
            self.validate()

    def test_insecure_source_rejected(self):
        self.record["source_url"] = "http://example.org/market/AMD"
        with self.assertRaisesRegex(ValueError, "invalid_source_url"):
            self.validate()

    def test_missing_source_rejected(self):
        self.record.pop("source_name")
        with self.assertRaisesRegex(ValueError, "missing_required_field_source_name"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
