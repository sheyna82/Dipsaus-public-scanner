import unittest
from research.spoor2_eu_tls_peer_binding_20261111 import review_eu_tls_peer_binding

class PeerBindingTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            selected_address="8.8.8.8",sni_hostname="data.example.org",
            certificate_hostname="data.example.org",certificate_validation=True,
            observed_peer_address="8.8.8.8",observed_peer_port=443,
            tls_hostname_checked=True,tls_chain_checked=True)
    def check_block(self,**kw):
        r=review_eu_tls_peer_binding(**{**self.args,**kw})
        self.assertEqual(r["status"],"BLOCKED")
        self.assertFalse(r["connection_authorized"])
    def test_matching_claims_never_authorize(self):
        r=review_eu_tls_peer_binding(**self.args)
        self.assertEqual(r["status"],"OFFLINE_PEER_CLAIMS_MATCH_ONLY")
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
    def test_peer_mismatch(self): self.check_block(observed_peer_address="1.1.1.1")
    def test_private_peer(self): self.check_block(observed_peer_address="127.0.0.1")
    def test_integer_peer(self): self.check_block(observed_peer_address=134744072)
    def test_whitespace_peer(self): self.check_block(observed_peer_address=" 8.8.8.8")
    def test_port_mismatch(self): self.check_block(observed_peer_port=8443)
    def test_boolean_port(self): self.check_block(observed_peer_port=True)
    def test_hostname_not_checked(self): self.check_block(tls_hostname_checked=False)
    def test_chain_not_checked(self): self.check_block(tls_chain_checked=False)
    def test_dns_reresolution(self): self.check_block(dns_reresolution_allowed=True)
    def test_redirects(self): self.check_block(redirects_allowed=True)
    def test_invalid_sni(self): self.check_block(sni_hostname="evil.test")
    def test_missing_peer(self): self.check_block(observed_peer_address=None)
if __name__=="__main__": unittest.main()
