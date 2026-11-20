import unittest
from research_attestation_chain import check_attestation_chain as check

def entry(n, previous=None):
    return {"sequence": n, "batch_digest": format(n, "064x"),
            "previous_digest": previous,
            "closed_utc": "2026-01-01T00:00:00Z",
            "attested_utc": "2026-01-01T00:10:00Z",
            "key_id": "synthetic-key",
            "signature_verified_externally": False}

class AttestationChainTests(unittest.TestCase):
    def test_structural_chain_never_proves_authenticity(self):
        r = check([entry(1), entry(2, format(1, "064x"))])
        self.assertEqual(r["status"], "ATTESTATION_CHAIN_STRUCTURALLY_CONSISTENT")
        self.assertFalse(r["attestation_independently_verified"])
        self.assertFalse(r["trade_ready"])

    def test_missing_sequence(self):
        self.assertEqual(check([entry(1), entry(3, format(1, "064x"))])["reason"],
                         "MISSING_DUPLICATE_OR_REORDERED_SEQUENCE")

    def test_duplicate_sequence(self):
        self.assertEqual(check([entry(1), entry(1, format(1, "064x"))])["reason"],
                         "MISSING_DUPLICATE_OR_REORDERED_SEQUENCE")

    def test_broken_link(self):
        self.assertEqual(check([entry(1), entry(2, "a" * 64)])["reason"],
                         "BROKEN_CHAIN_LINK")

    def test_wrong_genesis_link(self):
        self.assertEqual(check([entry(1, "a" * 64)])["reason"],
                         "BROKEN_CHAIN_LINK")

    def test_late_attestation(self):
        self.assertEqual(check([{**entry(1), "attested_utc":
                                 "2026-01-01T04:00:00Z"}])["reason"],
                         "INVALID_OR_LATE_ATTESTATION_TIME")

    def test_before_batch_close(self):
        self.assertEqual(check([{**entry(1), "attested_utc":
                                 "2025-12-31T23:59:00Z"}])["reason"],
                         "INVALID_OR_LATE_ATTESTATION_TIME")

    def test_claimed_signature_not_trusted(self):
        self.assertEqual(check([{**entry(1),
                                 "signature_verified_externally": True}])["reason"],
                         "UNTRUSTED_VERIFICATION_CLAIM")

    def test_unknown_field_blocked(self):
        self.assertEqual(check([{**entry(1), "ticker": "private"}])["reason"],
                         "INVALID_RECORD")

    def test_empty_chain_blocked(self):
        self.assertEqual(check([])["reason"], "INVALID_INPUT")

if __name__ == "__main__":
    unittest.main()
