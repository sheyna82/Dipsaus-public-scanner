import unittest
from research.spoor2_eu_source_separation_20261111 import audit_eu_source_separation

def fixture():
    return {r+"_evidence":{"provider_id":"provider-"+r,"source_family":"family-"+r,
                            "source_record_id":"record-"+r,
                            "source_url":"https://example.org/"+r}
            for r in ("ask","target_bid","invalidation","fx","fees")}

class EuSourceSeparationTests(unittest.TestCase):
    def test_distinct_metadata_still_unattested(self):
        r=audit_eu_source_separation(fixture())
        self.assertEqual(r["status"],"PROVENANCE_ONLY_NOT_ATTESTED")
        self.assertFalse(r["trade_ready"])
    def test_same_broker_provider_rejected(self):
        d=fixture()
        d["target_bid_evidence"]["provider_id"]=d["ask_evidence"]["provider_id"]
        self.assertIn("BROKER_TECHNICAL_SOURCE_NOT_SEPARATED",audit_eu_source_separation(d)["blocks"])
    def test_same_source_family_rejected(self):
        d=fixture()
        d["invalidation_evidence"]["source_family"]=d["ask_evidence"]["source_family"]
        self.assertIn("BROKER_TECHNICAL_SOURCE_NOT_SEPARATED",audit_eu_source_separation(d)["blocks"])
    def test_reused_record_rejected(self):
        d=fixture()
        d["target_bid_evidence"]["provider_id"]=d["ask_evidence"]["provider_id"]
        d["target_bid_evidence"]["source_record_id"]=d["ask_evidence"]["source_record_id"]
        self.assertIn("SOURCE_RECORD_REUSED",audit_eu_source_separation(d)["blocks"])
    def test_identical_url_rejected_despite_distinct_claimed_providers(self):
        d=fixture()
        d["target_bid_evidence"]["source_url"]=d["ask_evidence"]["source_url"]
        result=audit_eu_source_separation(d)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertIn("BROKER_TECHNICAL_SOURCE_URL_REUSED",result["blocks"])
        self.assertFalse(result["trade_ready"])
    def test_equivalent_https_host_case_and_default_port_rejected(self):
        d=fixture()
        d["ask_evidence"]["source_url"]="https://EXAMPLE.org:443/ask"
        d["target_bid_evidence"]["source_url"]="https://example.org/ask"
        result=audit_eu_source_separation(d)
        self.assertIn("BROKER_TECHNICAL_SOURCE_URL_REUSED",result["blocks"])
        self.assertFalse(result["trade_ready"])
    def test_equivalent_root_path_rejected(self):
        d=fixture()
        d["ask_evidence"]["source_url"]="https://example.org"
        d["invalidation_evidence"]["source_url"]="https://example.org/"
        self.assertIn("BROKER_TECHNICAL_SOURCE_URL_REUSED",
                      audit_eu_source_separation(d)["blocks"])
    def test_distinct_query_not_claimed_equivalent(self):
        d=fixture()
        d["ask_evidence"]["source_url"]="https://example.org/quotes?id=1"
        d["target_bid_evidence"]["source_url"]="https://example.org/quotes?id=2"
        result=audit_eu_source_separation(d)
        self.assertNotIn("BROKER_TECHNICAL_SOURCE_URL_REUSED",result["blocks"])
        self.assertFalse(result["trade_ready"])
    def test_distinct_paths_same_host_remain_unattested(self):
        result=audit_eu_source_separation(fixture())
        self.assertEqual(result["status"],"PROVENANCE_ONLY_NOT_ATTESTED")
        self.assertIn("EXTERNAL_SOURCE_ATTESTATION_NOT_CONNECTED",result["blocks"])
    def test_missing_family_rejected(self):
        d=fixture()
        del d["ask_evidence"]["source_family"]
        self.assertIn("ASK_SOURCE_IDENTITY_INCOMPLETE",audit_eu_source_separation(d)["blocks"])
    def test_bad_url_rejected(self):
        d=fixture()
        d["ask_evidence"]["source_url"]="https://user:pass@example.org/ask"
        self.assertIn("ASK_SOURCE_URL_INVALID",audit_eu_source_separation(d)["blocks"])
    def test_ambiguous_host_labels_fail_closed(self):
        for url in ("https://example..org/ask", "https://example.org../ask",
                    "https://./ask", "https://../ask"):
            with self.subTest(url=url):
                d=fixture()
                d["ask_evidence"]["source_url"]=url
                result=audit_eu_source_separation(d)
                self.assertIn("ASK_SOURCE_URL_INVALID",result["blocks"])
                self.assertEqual(result["status"],"BLOCKED")
                self.assertFalse(result["trade_ready"])
    def test_backslash_url_fails_closed(self):
        d=fixture()
        d["ask_evidence"]["source_url"]="https://example.org/ask\\\\other"
        result=audit_eu_source_separation(d)
        self.assertIn("ASK_SOURCE_URL_INVALID",result["blocks"])
        self.assertFalse(result["order_placement_enabled"])
    def test_bad_candidate_rejected(self):
        self.assertIn("INVALID_CANDIDATE",audit_eu_source_separation(None)["blocks"])

if __name__=="__main__":
    unittest.main()
