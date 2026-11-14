import unittest
from research.spoor2_eu_dns_provenance_20261111 import review_dns_provenance

class DNSProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            resolver_identity="resolver.example.org",
            observation_utc="2026-11-11T12:00:00Z")
    def test_claims_never_attest(self):
        r=review_dns_provenance(**self.args,claimed_dnssec=True,claimed_independent=True)
        self.assertEqual(r["status"],"OFFLINE_DNS_PROVENANCE_CLAIMS_ONLY")
        self.assertFalse(r["dns_attested"])
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
    def test_digest_stable(self):
        a=review_dns_provenance(**self.args)
        b=review_dns_provenance(**self.args)
        self.assertEqual(a["record_sha256"],b["record_sha256"])
    def test_private_ip_blocked(self):
        r=review_dns_provenance(**{**self.args,"resolved_addresses":["127.0.0.1"]})
        self.assertEqual(r["status"],"BLOCKED")
    def test_unallowed_host_blocked(self):
        r=review_dns_provenance(**{**self.args,"url":"https://evil.test"})
        self.assertEqual(r["status"],"BLOCKED")
    def test_missing_resolver_blocked(self):
        r=review_dns_provenance(**{**self.args,"resolver_identity":""})
        self.assertEqual(r["status"],"BLOCKED")
    def test_invalid_time_blocked(self):
        r=review_dns_provenance(**{**self.args,"observation_utc":"yesterday"})
        self.assertEqual(r["status"],"BLOCKED")
    def test_non_utc_blocked(self):
        r=review_dns_provenance(**{**self.args,"observation_utc":"2026-11-11T12:00:00+01:00"})
        self.assertEqual(r["status"],"BLOCKED")
if __name__=="__main__": unittest.main()
