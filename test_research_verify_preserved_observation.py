"""Regression checks for preserved AMD research observation."""
import tempfile
import unittest
from pathlib import Path
from research_verify_preserved_observation import verify_preserved_observation

SOURCE = Path(__file__).parent / "research-evidence/amd-20261103-source-observation.json"
JSON_DIGEST = "6de199463955abfc817c551c1cf3adb6f2f07ed06cf93e657497da3cae31e804"
RAW_DIGEST = "d0fc09361efffbcd4e001ca8f1c83f14b4f0f81da1eff9ac5113c586ed510e9a"

class PreservedObservationTests(unittest.TestCase):
    def test_real_committed_amd_bytes(self):
        report=verify_preserved_observation(SOURCE,expected_json_sha256=JSON_DIGEST,
                                             expected_source_sha256=RAW_DIGEST)
        self.assertEqual(report["symbol"],"AMD")
        self.assertFalse(report["trade_ready"])
    def test_tampered_bytes_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"modified.json"
            p.write_bytes(SOURCE.read_bytes()+b" ")
            with self.assertRaisesRegex(ValueError,"observation_json_hash_mismatch"):
                verify_preserved_observation(p,expected_json_sha256=JSON_DIGEST,
                                             expected_source_sha256=RAW_DIGEST)
    def test_wrong_expected_source_rejected(self):
        with self.assertRaisesRegex(ValueError,"observation_source_hash_mismatch"):
            verify_preserved_observation(SOURCE,expected_json_sha256=JSON_DIGEST,
                                         expected_source_sha256="0"*64)
    def test_bad_digest_rejected(self):
        with self.assertRaisesRegex(ValueError,"invalid_expected_json_digest"):
            verify_preserved_observation(SOURCE,expected_json_sha256="no",
                                         expected_source_sha256=RAW_DIGEST)

if __name__=="__main__": unittest.main()
