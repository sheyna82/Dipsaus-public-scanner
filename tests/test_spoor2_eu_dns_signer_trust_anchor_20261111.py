import base64
import unittest
from research.spoor2_eu_dns_signer_trust_anchor_20261111 import review_dns_signer_trust_anchor

class DNSAnchorTests(unittest.TestCase):
    def test_unapproved_key_fails_closed(self):
        r=review_dns_signer_trust_anchor(base64.b64encode(b"x"*32).decode())
        self.assertEqual(r["blocks"],["SIGNER_KEY_NOT_INDEPENDENTLY_APPROVED"])
        self.assertFalse(r["key_trusted"])
        self.assertFalse(r["dns_admitted"])
    def test_invalid_base64_rejected(self):
        r=review_dns_signer_trust_anchor("%%%")
        self.assertEqual(r["blocks"],["INVALID_SIGNER_PUBLIC_KEY"])
    def test_short_key_rejected(self):
        r=review_dns_signer_trust_anchor(base64.b64encode(b"x"*4).decode())
        self.assertEqual(r["blocks"],["INVALID_SIGNER_PUBLIC_KEY"])
    def test_non_string_rejected(self):
        r=review_dns_signer_trust_anchor(None)
        self.assertEqual(r["blocks"],["INVALID_SIGNER_PUBLIC_KEY"])
if __name__=="__main__": unittest.main()
