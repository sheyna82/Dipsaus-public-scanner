import unittest
from research_synthetic_hmac import synthetic_mac, verify_synthetic_mac

KEY = b"synthetic-test-key-material-not-a-production-secret"
D = "a" * 64

class SyntheticHmacTests(unittest.TestCase):
    def test_valid_mac_is_not_independent_attestation(self):
        tag = synthetic_mac(D, synthetic_key=KEY)["tag"]
        r = verify_synthetic_mac(D, tag, synthetic_key=KEY)
        self.assertEqual(r["status"], "SYNTHETIC_MAC_MATCH")
        self.assertTrue(r["tag_matches"])
        self.assertFalse(r["independently_authenticated"])
        self.assertFalse(r["trade_ready"])

    def test_changed_batch_detected(self):
        tag = synthetic_mac(D, synthetic_key=KEY)["tag"]
        self.assertEqual(verify_synthetic_mac("b"*64, tag, synthetic_key=KEY)["status"],
                         "SYNTHETIC_MAC_MISMATCH")

    def test_changed_tag_detected(self):
        tag = synthetic_mac(D, synthetic_key=KEY)["tag"]
        self.assertFalse(verify_synthetic_mac(D, "0"*64, synthetic_key=KEY)
                         ["tag_matches"])

    def test_wrong_key_detected(self):
        tag = synthetic_mac(D, synthetic_key=KEY)["tag"]
        self.assertFalse(verify_synthetic_mac(
            D, tag, synthetic_key=b"different-synthetic-test-key-material-0000")
            ["tag_matches"])

    def test_short_key_blocked(self):
        self.assertEqual(synthetic_mac(D, synthetic_key=b"short")["reason"],
                         "INVALID_DIGEST_OR_KEY")

    def test_invalid_digest_blocked(self):
        self.assertEqual(synthetic_mac("not-a-digest", synthetic_key=KEY)["reason"],
                         "INVALID_DIGEST_OR_KEY")

    def test_invalid_tag_blocked(self):
        self.assertEqual(verify_synthetic_mac(D, "bad", synthetic_key=KEY)["reason"],
                         "INVALID_TAG")

if __name__ == "__main__":
    unittest.main()
