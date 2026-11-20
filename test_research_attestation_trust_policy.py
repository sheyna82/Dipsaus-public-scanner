import unittest
from research_attestation_trust_policy import assess_verifier_evidence as assess

E = {"batch_digest": "a"*64, "reference_digest": "a"*64,
     "key_id": "synthetic-key", "verification_utc": "2026-01-01T00:00:00Z",
     "signature_valid": True, "key_revoked": False, "trusted_verifier": True}
def check(evidence=E, keys=("synthetic-key",)):
    return assess(evidence, trusted_key_ids=keys)

class TrustPolicyTests(unittest.TestCase):
    def test_matching_self_report_is_not_cryptographic_proof(self):
        r = check()
        self.assertEqual(r["status"], "ATTESTATION_CLAIMS_STRUCTURALLY_ACCEPTED")
        self.assertFalse(r["independent_signature_verified"])
        self.assertFalse(r["trade_ready"])

    def test_untrusted_key(self):
        self.assertEqual(check(keys=("other",))["reason"], "UNTRUSTED_KEY")

    def test_revoked_key(self):
        self.assertEqual(check({**E, "key_revoked": True})["reason"],
                         "KEY_REVOKED_OR_UNKNOWN")

    def test_bad_signature(self):
        self.assertEqual(check({**E, "signature_valid": False})["reason"],
                         "SIGNATURE_INVALID_OR_UNKNOWN")

    def test_unknown_verifier(self):
        self.assertEqual(check({**E, "trusted_verifier": False})["reason"],
                         "UNTRUSTED_VERIFIER")

    def test_changed_digest(self):
        self.assertEqual(check({**E, "reference_digest": "b"*64})["reason"],
                         "REFERENCE_DIGEST_MISMATCH")

    def test_missing_timestamp(self):
        self.assertEqual(check({**E, "verification_utc": None})["reason"],
                         "INVALID_VERIFICATION_TIME")

    def test_extra_private_field(self):
        self.assertEqual(check({**E, "ticker": "private"})["reason"],
                         "INVALID_VERIFIER_INPUT")

if __name__ == "__main__":
    unittest.main()
