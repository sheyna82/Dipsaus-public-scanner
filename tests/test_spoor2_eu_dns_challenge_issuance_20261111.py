import os
import tempfile
import unittest
from research.spoor2_eu_dns_challenge_issuance_20261111 import issue_dns_challenge,review_dns_challenge_issuance

class ChallengeIssuanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=os.path.join(self.tmp.name,"issued.sqlite3")
        self.nonce="a"*64
    def test_unissued_challenge_rejected(self):
        r=review_dns_challenge_issuance(self.db,nonce=self.nonce)
        self.assertEqual(r["blocks"],["ISSUANCE_LEDGER_UNAVAILABLE"])
    def test_issued_challenge_still_untrusted(self):
        issue_dns_challenge(self.db,nonce=self.nonce,issuer_id="local-issuer-claim")
        r=review_dns_challenge_issuance(self.db,nonce=self.nonce)
        self.assertTrue(r["issued"])
        self.assertFalse(r["issuer_attested"])
        self.assertFalse(r["dns_admitted"])
    def test_duplicate_issue_rejected(self):
        issue_dns_challenge(self.db,nonce=self.nonce,issuer_id="local-issuer-claim")
        r=issue_dns_challenge(self.db,nonce=self.nonce,issuer_id="another")
        self.assertEqual(r["blocks"],["NONCE_ALREADY_ISSUED"])
    def test_unknown_nonce_rejected(self):
        issue_dns_challenge(self.db,nonce=self.nonce,issuer_id="local-issuer-claim")
        r=review_dns_challenge_issuance(self.db,nonce="b"*64)
        self.assertEqual(r["blocks"],["CHALLENGE_NOT_ISSUED"])
    def test_invalid_issuer_rejected(self):
        r=issue_dns_challenge(self.db,nonce=self.nonce,issuer_id=" ")
        self.assertEqual(r["blocks"],["INVALID_ISSUER_CLAIM"])
if __name__=="__main__": unittest.main()
