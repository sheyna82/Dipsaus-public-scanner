"""Synthetic-only external pin checks."""
import unittest
from research.us_observation_chain_20261118 import append_observation, verify_chain
from research.us_observation_external_pin_20261118 import verify_pinned_head

def chain():
    return append_observation([], {"symbol": "SYNTH", "source_id": "fixture",
        "observed_utc": "2026-11-17T21:00:00Z", "close_usd": 101})["chain"]

def pin(c):
    v = verify_chain(c)
    return {"expected_head_sha256": v["head_hash"], "expected_count": v["count"],
            "external_reference": "synthetic-external-reference"}

class ExternalPinTests(unittest.TestCase):
    def test_valid_pin_not_attestation(self):
        c = chain()
        x = verify_pinned_head(c, pin(c))
        self.assertEqual(x["status"], "CONSISTENT_WITH_SUPPLIED_PIN")
        self.assertIn("PIN_INDEPENDENCE_NOT_ATTESTED", x["blocks"])
        self.assertFalse(x["trade_ready"])

    def test_missing_pin(self):
        self.assertEqual(verify_pinned_head(chain(), None)["status"], "BLOCKED")

    def test_rewritten_chain_detected_against_old_pin(self):
        c = chain()
        p = pin(c)
        altered = chain()
        altered[0]["close_usd"] = 103
        from research.us_observation_chain_20261118 import _digest
        altered[0]["hash"] = _digest({k: v for k, v in altered[0].items() if k != "hash"})
        self.assertEqual(verify_chain(altered)["status"], "VALID")
        self.assertIn("EXTERNAL_PIN_MISMATCH", verify_pinned_head(altered, p)["blocks"])

    def test_invalid_hash(self):
        c = chain()
        p = pin(c)
        p["expected_head_sha256"] = "abc"
        self.assertEqual(verify_pinned_head(c, p)["status"], "BLOCKED")

    def test_count_mismatch(self):
        c = chain()
        p = pin(c)
        p["expected_count"] = 2
        self.assertIn("EXTERNAL_PIN_MISMATCH", verify_pinned_head(c, p)["blocks"])

    def test_empty_chain_blocked(self):
        self.assertEqual(verify_pinned_head([], {"expected_head_sha256": "a"*64,
            "expected_count": 0, "external_reference": "fixture"})["status"], "BLOCKED")

    def test_reference_missing(self):
        c = chain()
        p = pin(c)
        p["external_reference"] = ""
        self.assertEqual(verify_pinned_head(c, p)["status"], "BLOCKED")

    def test_boolean_count_blocked(self):
        c = chain()
        p = pin(c)
        p["expected_count"] = True
        self.assertEqual(verify_pinned_head(c, p)["status"], "BLOCKED")

if __name__ == "__main__":
    unittest.main()
