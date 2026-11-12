import unittest
from research.spoor2_instrument_observation_window_20261112 import (
    audit_instrument_observation_window as audit,
)
NONCE = "a" * 32
OBS = "2026-11-12T10:00:00Z"


class InstrumentObservationWindowTests(unittest.TestCase):
    def test_consistent_window_still_blocks_replay(self):
        r = audit(OBS, "2026-11-12T10:04:00Z", NONCE)
        self.assertEqual(r["status"], "TIME_WINDOW_CLAIMS_CONSISTENT_ONLY")
        self.assertFalse(r["freshness_attested"])
        self.assertFalse(r["replay_prevented"])
        self.assertIn("INSTRUMENT_NONCE_SINGLE_USE_NOT_ENFORCED", r["blocks"])

    def test_stale_observation_blocks(self):
        self.assertIn("INSTRUMENT_OBSERVATION_OUTSIDE_WINDOW",
                      audit(OBS, "2026-11-12T10:06:00Z", NONCE)["blocks"])

    def test_future_observation_blocks(self):
        self.assertIn("INSTRUMENT_OBSERVATION_OUTSIDE_WINDOW",
                      audit(OBS, "2026-11-12T09:59:00Z", NONCE)["blocks"])

    def test_invalid_nonce_blocks(self):
        self.assertIn("INSTRUMENT_CHALLENGE_INVALID",
                      audit(OBS, OBS, "guessable")["blocks"])

    def test_naive_timestamp_blocks(self):
        self.assertIn("INSTRUMENT_OBSERVATION_TIME_INVALID",
                      audit("2026-11-12T10:00:00", OBS, NONCE)["blocks"])

    def test_invalid_policy_blocks(self):
        self.assertIn("INVALID_INSTRUMENT_AGE_POLICY",
                      audit(OBS, OBS, NONCE, max_age_seconds=True)["blocks"])


if __name__ == "__main__":
    unittest.main()
