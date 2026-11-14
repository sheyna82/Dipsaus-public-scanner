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

    def test_url_host_case_default_port_and_fragment_cannot_mask_reuse(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://EXAMPLE.ORG:443/record/broker/#first")
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/record/broker#second")
        self.assertIn("SOURCE_RECORD_REUSED",
                      audit_source_independence(data)["blocks"])

    def test_query_parameter_order_cannot_mask_reuse(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/history?symbol=ABC&date=2026-11-11")
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/history?date=2026-11-11&symbol=ABC")
        self.assertIn("SOURCE_RECORD_REUSED",
                      audit_source_independence(data)["blocks"])

    def test_distinct_query_addressed_records_are_not_collapsed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/history?record=broker")
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/history?record=resistance")
        self.assertNotIn("SOURCE_RECORD_REUSED",
                         audit_source_independence(data)["blocks"])

    def test_malformed_port_fails_closed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org:invalid/record")
        self.assertIn("BROKER_SOURCE_URL_INVALID",
                      audit_source_independence(data)["blocks"])

    def test_unreserved_percent_encoding_cannot_mask_reused_url(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/record/%62roker")
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/record/broker")
        self.assertIn("SOURCE_RECORD_REUSED",
                      audit_source_independence(data)["blocks"])

    def test_reserved_encoded_slash_is_not_silently_decoded(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/record%2Fbroker")
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/record/broker")
        self.assertNotIn("SOURCE_RECORD_REUSED",
                         audit_source_independence(data)["blocks"])

    def test_invalid_port_does_not_produce_spurious_reuse_finding(self):
        data = sample()
        data["broker_evidence"]["source_url"] = "https://example.org:bad/record"
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertNotIn("SOURCE_RECORD_REUSED", result["blocks"])

    def test_same_provider_with_conflicting_families_blocks(self):
        data = sample()
        data["resistance_evidence"]["source_family"] = "vendor"
        result = audit_source_independence(data)
        self.assertIn("PROVIDER_SOURCE_FAMILY_CONFLICT", result["blocks"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["trade_ready"])

    def test_same_provider_same_family_with_distinct_records_remains_valid(self):
        result = audit_source_independence(sample())
        self.assertNotIn("PROVIDER_SOURCE_FAMILY_CONFLICT", result["blocks"])
        self.assertEqual(result["status"],
                         "PROVENANCE_RECORDED_REQUIRES_EXTERNAL_VERIFICATION")

    def test_duplicate_query_keys_fail_closed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/quote?symbol=ABC&symbol=XYZ")
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_QUERY_AMBIGUOUS", result["blocks"])
        self.assertEqual(result["status"], "BLOCKED")
        self.assertFalse(result["trade_ready"])

    def test_distinct_query_keys_remain_inspectable(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/quote?symbol=ABC&date=2026-11-12")
        result = audit_source_independence(data)
        self.assertNotIn("BROKER_SOURCE_QUERY_AMBIGUOUS", result["blocks"])
        self.assertEqual(result["status"],
                         "PROVENANCE_RECORDED_REQUIRES_EXTERNAL_VERIFICATION")

    def test_malformed_percent_escape_blocks_provenance(self):
        data = sample()
        data["broker_evidence"]["source_url"] = "https://example.org/quote%ZZ"
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_encoded_control_character_blocks_provenance(self):
        data = sample()
        data["resistance_evidence"]["source_url"] = (
            "https://example.org/quote%0Ahidden")
        result = audit_source_independence(data)
        self.assertIn("RESISTANCE_SOURCE_URL_INVALID", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_valid_percent_encoded_unreserved_path_remains_accepted(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/record/%62roker")
        result = audit_source_independence(data)
        self.assertNotIn("BROKER_SOURCE_URL_INVALID", result["blocks"])

    def test_unclosed_ipv6_authority_fails_closed_without_exception(self):
        data = sample()
        data["broker_evidence"]["source_url"] = "https://[::1/quote"
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_invalid_ipv6_authority_fails_closed_without_exception(self):
        data = sample()
        data["broker_evidence"]["source_url"] = "https://[not-ipv6]/quote"
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_raw_newline_in_source_url_fails_closed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/quote\n?symbol=ABC")
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertFalse(result["trade_ready"])

    def test_surrounding_url_whitespace_fails_closed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            " https://example.org/quote ")
        result = audit_source_independence(data)
        self.assertIn("BROKER_SOURCE_URL_INVALID", result["blocks"])
        self.assertEqual(result["status"], "BLOCKED")

    def test_raw_delete_control_in_url_fails_closed(self):
        data = sample()
        data["broker_evidence"]["source_url"] = (
            "https://example.org/quote\x7f")
        self.assertIn("BROKER_SOURCE_URL_INVALID",
                      audit_source_independence(data)["blocks"])

    def test_bogus_input_fails_closed(self):
        self.assertEqual(audit_source_independence(None)["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
