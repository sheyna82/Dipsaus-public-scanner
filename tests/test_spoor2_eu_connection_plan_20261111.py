import unittest
from research.spoor2_eu_connection_plan_20261111 import review_eu_connection_plan
URL="https://data.example.org/quote"
HOSTS=("data.example.org",)
def check(url=URL, addresses=None, hosts=HOSTS):
    return review_eu_connection_plan(url,allowed_hosts=hosts,
        resolved_addresses=["8.8.8.8"] if addresses is None else addresses)
class ConnectionPlanTests(unittest.TestCase):
    def test_public_ip_and_host_still_unattested(self):
        r=check()
        self.assertEqual(r["status"],"OFFLINE_CONNECTION_PLAN_ONLY")
        self.assertFalse(r["connection_authorized"])
        self.assertFalse(r["trade_ready"])
        self.assertIn("PINNED_TLS_CONNECTION_NOT_VERIFIED",r["blocks"])
    def test_private_ip_blocks(self):
        r=check(addresses=["10.0.0.2"])
        self.assertEqual(r["status"],"BLOCKED")
        self.assertIn("NON_PUBLIC_RESOLVED_ADDRESS",r["blocks"])
    def test_mixed_addresses_blocks(self):
        self.assertEqual(check(addresses=["8.8.8.8","127.0.0.1"])["status"],"BLOCKED")
    def test_wrong_host_blocks_before_ip_review(self):
        r=check(url="https://other.example.org/quote")
        self.assertIn("HOST_NOT_ALLOWLISTED",r["blocks"])
        self.assertNotIn("address_review",r)
    def test_http_blocks(self):
        self.assertIn("UNSAFE_URL",check(url="http://data.example.org/quote")["blocks"])
    def test_empty_resolution_blocks(self):
        self.assertIn("INVALID_RESOLUTION_SET",check(addresses=[])["blocks"])
    def test_ipv6_public_still_unattested(self):
        self.assertEqual(check(addresses=["2606:4700:4700::1111"])["status"],"OFFLINE_CONNECTION_PLAN_ONLY")
if __name__=="__main__":
    unittest.main()
