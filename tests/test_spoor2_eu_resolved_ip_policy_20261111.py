import unittest
from research.spoor2_eu_resolved_ip_policy_20261111 import review_resolved_addresses as check
class ResolvedIpPolicyTests(unittest.TestCase):
    def test_public_ipv4_review_only(self):
        r=check(["8.8.8.8"])
        self.assertEqual(r["status"],"OFFLINE_PUBLIC_IP_REVIEW_ONLY")
        self.assertFalse(r["connection_authorized"])
    def test_public_ipv6_review_only(self):
        r=check(["2606:4700:4700::1111"])
        self.assertEqual(r["status"],"OFFLINE_PUBLIC_IP_REVIEW_ONLY")
    def test_loopback_blocked(self):
        self.assertIn("NON_PUBLIC_RESOLVED_ADDRESS",check(["127.0.0.1"])["blocks"])
    def test_private_blocked(self):
        self.assertIn("NON_PUBLIC_RESOLVED_ADDRESS",check(["10.1.2.3"])["blocks"])
    def test_link_local_metadata_blocked(self):
        self.assertIn("NON_PUBLIC_RESOLVED_ADDRESS",check(["169.254.169.254"])["blocks"])
    def test_mixed_public_private_fails_entire_set(self):
        self.assertEqual(check(["8.8.8.8","192.168.1.2"])["status"],"BLOCKED")
    def test_ipv6_mapped_ipv4_blocked(self):
        self.assertIn("EMBEDDED_IPV4_ADDRESS_REJECTED",check(["::ffff:8.8.8.8"])["blocks"])
    def test_duplicate_blocked(self):
        self.assertIn("DUPLICATE_RESOLVED_ADDRESS",check(["8.8.8.8","8.8.8.8"])["blocks"])
    def test_invalid_address_blocked(self):
        self.assertIn("INVALID_RESOLVED_ADDRESS",check(["example.org"])["blocks"])
    def test_empty_resolution_blocked(self):
        self.assertIn("INVALID_RESOLUTION_SET",check([])["blocks"])
if __name__=="__main__":
    unittest.main()
