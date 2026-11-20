import hashlib
import unittest
from research_key_rotation_policy import assess_key_rotation as assess

PEM = b"-----BEGIN PUBLIC KEY-----\nsynthetic-placeholder\n-----END PUBLIC KEY-----\n"
FP = hashlib.sha256(PEM).hexdigest()
KEY = {"key_id": "key-1", "public_key_pem": PEM,
       "valid_from_utc": "2026-01-01T00:00:00Z",
       "valid_until_utc": "2026-02-01T00:00:00Z",
       "revoked_from_utc": None}
def check(keys=None, at="2026-01-15T00:00:00Z", key_id="key-1", fp=FP):
    return assess([KEY] if keys is None else keys, key_id=key_id,
                  attested_utc=at, expected_public_key_sha256=fp)

class KeyRotationPolicyTests(unittest.TestCase):
    def test_in_window_still_not_independently_trusted(self):
        r = check()
        self.assertEqual(r["status"], "KEY_POLICY_STRUCTURALLY_ACCEPTED")
        self.assertFalse(r["independently_trusted_key"])
        self.assertFalse(r["trade_ready"])

    def test_expired_key(self):
        self.assertEqual(check(at="2026-02-02T00:00:00Z")["reason"],
                         "KEY_NOT_VALID_AT_ATTESTATION")

    def test_not_yet_valid_key(self):
        self.assertEqual(check(at="2025-12-31T00:00:00Z")["reason"],
                         "KEY_NOT_VALID_AT_ATTESTATION")

    def test_revoked_key(self):
        k = {**KEY, "revoked_from_utc": "2026-01-10T00:00:00Z"}
        self.assertEqual(check(keys=[k])["reason"], "KEY_REVOKED_AT_ATTESTATION")

    def test_pre_revocation_is_structurally_allowed(self):
        k = {**KEY, "revoked_from_utc": "2026-01-20T00:00:00Z"}
        self.assertEqual(check(keys=[k])["status"],
                         "KEY_POLICY_STRUCTURALLY_ACCEPTED")

    def test_wrong_key_fingerprint(self):
        self.assertEqual(check(fp="a"*64)["reason"], "KEY_FINGERPRINT_MISMATCH")

    def test_unknown_key(self):
        self.assertEqual(check(key_id="key-2")["reason"], "UNKNOWN_KEY")

    def test_duplicate_key(self):
        self.assertEqual(check(keys=[KEY, KEY])["reason"],
                         "DUPLICATE_OR_INVALID_KEY_ID")

    def test_invalid_revocation_timestamp(self):
        k = {**KEY, "revoked_from_utc": "not-a-time"}
        self.assertEqual(check(keys=[k])["reason"], "INVALID_KEY_WINDOW")

if __name__ == "__main__":
    unittest.main()
