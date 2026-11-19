import unittest
from research.spoor2_eu_dns_signer_approval_20261111 import review_dns_signer_approval_proposal
from research.spoor2_eu_dns_signer_trust_anchor_20261111 import APPROVED_DNS_SIGNER_KEY_SHA256

class SignerApprovalTests(unittest.TestCase):
    def setUp(self):
        self.proposal=dict(signer_key_sha256="a"*64,source_uri="https://example.org/key",
            source_sha256="b"*64,reviewer_1="reviewer-a",reviewer_2="reviewer-b",
            reviewed_at_utc="2026-11-11T12:00:00Z",hostname_scope="data.example.org",
            rotation_policy="manual review",revocation_policy="revoke on compromise")
    def test_complete_proposal_never_grants_trust(self):
        r=review_dns_signer_approval_proposal(self.proposal)
        self.assertEqual(r["status"],"SIGNER_APPROVAL_PROPOSAL_ONLY")
        self.assertFalse(r["approval_granted"])
        self.assertFalse(r["key_trusted"])
        self.assertFalse(r["dns_admitted"])
        self.assertEqual(APPROVED_DNS_SIGNER_KEY_SHA256,frozenset())
    def test_same_reviewer_rejected(self):
        r=review_dns_signer_approval_proposal({**self.proposal,"reviewer_2":"reviewer-a"})
        self.assertEqual(r["blocks"],["NON_INDEPENDENT_APPROVAL_REVIEWERS"])
    def test_missing_evidence_rejected(self):
        r=review_dns_signer_approval_proposal({"signer_key_sha256":"a"*64})
        self.assertEqual(r["blocks"],["INCOMPLETE_SIGNER_APPROVAL_PROPOSAL"])
    def test_invalid_fingerprint_rejected(self):
        r=review_dns_signer_approval_proposal({**self.proposal,"source_sha256":"invalid"})
        self.assertEqual(r["blocks"],["INVALID_SIGNER_APPROVAL_FINGERPRINT"])
    def test_proposal_hash_deterministic(self):
        a=review_dns_signer_approval_proposal(self.proposal)
        c=review_dns_signer_approval_proposal(dict(reversed(list(self.proposal.items()))))
        self.assertEqual(a["proposal_sha256"],c["proposal_sha256"])
if __name__=="__main__": unittest.main()
