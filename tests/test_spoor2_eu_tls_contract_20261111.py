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
    def test_integer_address_cannot_bypass_text_contract(self): self.check_block(selected_address=134744072)
    def test_boolean_address_rejected(self): self.check_block(selected_address=True)
    def test_whitespace_address_rejected(self): self.check_block(selected_address=" 8.8.8.8")
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
    def test_dns_answer_order_does_not_change_contract_digest(self):
        first=review_eu_tls_contract(**{**self.args,
            "resolved_addresses":["8.8.8.8","1.1.1.1"]})
        reverse=review_eu_tls_contract(**{**self.args,
            "resolved_addresses":["1.1.1.1","8.8.8.8"]})
        self.assertEqual(first["status"],"OFFLINE_TLS_CONTRACT_ONLY")
        self.assertEqual(first["contract"],reverse["contract"])
        self.assertEqual(first["contract_sha256"],reverse["contract_sha256"])
        self.assertFalse(reverse["connection_authorized"])
    def test_different_dns_set_changes_contract_digest(self):
        first=review_eu_tls_contract(**self.args)
        changed=review_eu_tls_contract(**{**self.args,
            "resolved_addresses":["8.8.8.8","1.1.1.1"]})
        self.assertNotEqual(first["contract_sha256"],changed["contract_sha256"])
        self.assertFalse(changed["trade_ready"])
    def test_claimed_tls_verified_cannot_change_contract_or_authorize(self):
        false_claim=review_eu_tls_contract(**self.args,claimed_tls_verified=False)
        true_claim=review_eu_tls_contract(**self.args,claimed_tls_verified=True)
        self.assertEqual(false_claim["contract_sha256"],true_claim["contract_sha256"])
        self.assertEqual(false_claim["status"],true_claim["status"])
        self.assertFalse(true_claim["connection_authorized"])
    def test_disallowed_host(self): self.check_block(url="https://evil.test")
if __name__=="__main__": unittest.main()
