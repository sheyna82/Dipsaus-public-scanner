import unittest
from research.spoor2_eu_dns_evidence_admission_20261111 import review_dns_evidence_admission

class DNSEvidenceAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            resolver_identity="resolver.example.org",
            observation_utc="2026-11-11T12:00:00Z")
    def test_missing_evidence_blocks(self):
        r=review_dns_evidence_admission(**self.args)
        self.assertEqual(r["blocks"],["MISSING_EXTERNAL_DNS_EVIDENCE"])
    def test_incomplete_evidence_blocks(self):
        r=review_dns_evidence_admission(**self.args,evidence={"resolver_signature":"claimed"})
        self.assertEqual(r["blocks"],["INCOMPLETE_EXTERNAL_DNS_EVIDENCE"])
    def test_complete_claims_do_not_admit(self):
        e={k:"self-asserted" for k in ("resolver_signature","resolver_public_key",
                                     "signed_response","verification_receipt")}
        r=review_dns_evidence_admission(**self.args,evidence=e)
        self.assertEqual(r["status"],"EXTERNAL_DNS_EVIDENCE_PRESENT_UNVERIFIED")
        self.assertFalse(r["dns_admitted"])
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
    def test_private_address_blocks(self):
        r=review_dns_evidence_admission(**{**self.args,"resolved_addresses":["127.0.0.1"]})
        self.assertEqual(r["status"],"BLOCKED")
    def test_invalid_evidence_type_blocks(self):
        r=review_dns_evidence_admission(**self.args,evidence="signed")
        self.assertEqual(r["blocks"],["INVALID_EXTERNAL_DNS_EVIDENCE"])
    def test_empty_claim_blocks(self):
        e={k:"x" for k in ("resolver_signature","resolver_public_key",
                           "signed_response","verification_receipt")}
        e["resolver_signature"]=" "
        r=review_dns_evidence_admission(**self.args,evidence=e)
        self.assertEqual(r["blocks"],["INCOMPLETE_EXTERNAL_DNS_EVIDENCE"])
if __name__=="__main__": unittest.main()
