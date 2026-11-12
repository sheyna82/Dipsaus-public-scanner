import unittest
from research.spoor2_source_independence_20261111 import audit_source_independence

def sample():
    return {
        role + "_evidence": {
            "provider_id": provider,
            "source_family": family,
            "source_record_id": role + "-20261111",
            "source_url": "https://example.org/record/" + role,
            "verified": True,
        }
        for role, provider, family in (
            ("broker", "broker-feed", "broker"),
            ("invalidation", "historical-venue", "exchange"),
            ("resistance", "historical-venue", "exchange"),
        )
    }

class SourceIndependenceTests(unittest.TestCase):
    def test_distinct_provider_families_remain_research_only(self):
        result = audit_source_independence(sample())
        self.assertEqual(result["status"], "PROVENANCE_RECORDED_REQUIRES_EXTERNAL_VERIFICATION")
        self.assertFalse(result["trade_ready"])

    def test_same_provider_blocks(self):
        data = sample()
        data["invalidation_evidence"]["provider_id"] = "broker-feed"
        self.assertIn("BROKER_TECHNICAL_PROVIDER_NOT_INDEPENDENT",
                      audit_source_independence(data)["blocks"])

    def test_same_family_blocks(self):
        data = sample()
        data["resistance_evidence"]["source_family"] = "broker"
        self.assertIn("BROKER_TECHNICAL_SOURCE_FAMILY_NOT_INDEPENDENT",
                      audit_source_independence(data)["blocks"])

    def test_uninspectable_url_blocks_even_if_verified(self):
        data = sample()
        data["broker_evidence"]["source_url"] = "http://example.org"
        self.assertIn("BROKER_SOURCE_URL_INVALID", audit_source_independence(data)["blocks"])

    def test_missing_record_blocks(self):
        data = sample()
        del data["broker_evidence"]["source_record_id"]
        self.assertIn("BROKER_PROVENANCE_INCOMPLETE", audit_source_independence(data)["blocks"])

    def test_record_id_reuse_blocks_even_with_different_provider_alias(self):
        data = sample()
        data["resistance_evidence"]["source_record_id"] = (
            data["broker_evidence"]["source_record_id"])
        self.assertIn("SOURCE_RECORD_REUSED",
                      audit_source_independence(data)["blocks"])

    def test_source_url_reuse_blocks_even_with_different_record_id(self):
        data = sample()
        data["resistance_evidence"]["source_url"] = (
            data["broker_evidence"]["source_url"])
        self.assertIn("SOURCE_RECORD_REUSED",
                      audit_source_independence(data)["blocks"])

    def test_distinct_technical_records_on_same_venue_are_allowed(self):
        data = sample()
        result = audit_source_independence(data)
        self.assertNotIn("SOURCE_RECORD_REUSED", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_bogus_input_fails_closed(self):
        self.assertEqual(audit_source_independence(None)["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
