import unittest
from research.spoor2_eu_tls_contract_20261111 import review_eu_tls_contract

class TLSContractTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",allowed_hosts=["data.example.org"],
            resolved_addresses=["8.8.8.8"],selected_address="8.8.8.8",
            sni_hostname="data.example.org",certificate_hostname="data.example.org",
            certificate_validation=True)
    def check_block(self, **updates):
        args={**self.args,**updates}
        result=review_eu_tls_contract(**args)
        self.assertEqual(result["status"],"BLOCKED")
        self.assertFalse(result["connection_authorized"])
    def test_valid_offline_never_authorized(self):
        r=review_eu_tls_contract(**self.args,claimed_tls_verified=True)
        self.assertEqual(r["status"],"OFFLINE_TLS_CONTRACT_ONLY")
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
    def test_unpinned_address(self): self.check_block(selected_address="1.1.1.1")
    def test_private_address(self): self.check_block(resolved_addresses=["127.0.0.1"],selected_address="127.0.0.1")
    def test_sni_mismatch(self): self.check_block(sni_hostname="evil.test")
    def test_cert_hostname_mismatch(self): self.check_block(certificate_hostname="evil.test")
    def test_missing_cert_validation(self): self.check_block(certificate_validation=False)
    def test_redirect(self): self.check_block(redirects_allowed=True)
    def test_dns_reresolution(self): self.check_block(dns_reresolution_allowed=True)
    def test_missing_selected_address(self): self.check_block(selected_address=None)
    def test_invalid_timeout(self): self.check_block(timeout_seconds=0)
    def test_invalid_size(self): self.check_block(max_response_bytes=0)
    def test_contract_tamper(self): self.check_block(plan_digest="0"*64)
    def test_digest_reproducible(self):
        a=review_eu_tls_contract(**self.args)
        b=review_eu_tls_contract(**self.args,plan_digest=a["contract_sha256"])
        self.assertEqual(a["contract_sha256"],b["contract_sha256"])
    def test_disallowed_host(self): self.check_block(url="https://evil.test")
if __name__=="__main__": unittest.main()
