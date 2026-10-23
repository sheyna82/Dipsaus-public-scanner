import hashlib
import tempfile
import unittest
from pathlib import Path
from research_calendar_wheel_integrity import verify_wheel


class WheelIntegrityTests(unittest.TestCase):
    def test_hash_matching_does_not_claim_security_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exchange_calendars-4.13.2-py3-none-any.whl"
            path.write_bytes(b"test wheel placeholder, not a real package")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result = verify_wheel(path, digest)
            self.assertTrue(result["sha256_verified"])
            self.assertFalse(result["production_approved"])
            self.assertFalse(result["vulnerability_scan_complete"])

    def test_rejects_mismatched_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exchange_calendars-4.13.2-py3-none-any.whl"
            path.write_bytes(b"fixture")
            with self.assertRaisesRegex(ValueError, "wheel_hash_mismatch"):
                verify_wheel(path, "0" * 64)

    def test_rejects_other_version(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "exchange_calendars-4.13.1-py3-none-any.whl"
            path.write_bytes(b"fixture")
            with self.assertRaisesRegex(ValueError, "unexpected_wheel_version"):
                verify_wheel(path, hashlib.sha256(b"fixture").hexdigest())


if __name__ == "__main__":
    unittest.main()
