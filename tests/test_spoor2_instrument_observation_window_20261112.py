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


    def test_oversized_timestamp_is_rejected_before_parse(self):
        r = audit("2026-11-12T10:00:00Z" + "0" * 100000, OBS, NONCE)
        self.assertIn("INSTRUMENT_OBSERVATION_TIME_OVERSIZED", r["blocks"])
        self.assertFalse(r["freshness_attested"])


    def test_noncanonical_utc_timestamps_block(self):
        invalid = (
            "2026-11-12 10:00:00Z",
            "2026-11-12t10:00:00Z",
            "20261112T100000Z",
            "2026-11-12T10:00Z",
            "2026-11-12T10:00:00.1234567Z",
            "2026-11-12T10:00:00+00:00",
            "2026-11-12T10:00:00Z ",
        )
        for timestamp in invalid:
            with self.subTest(timestamp=timestamp):
                r = audit(timestamp, OBS, NONCE)
                self.assertIn("INSTRUMENT_OBSERVATION_TIME_INVALID", r["blocks"])
                self.assertFalse(r["freshness_attested"])
                self.assertFalse(r["trade_ready"])

    def test_canonical_fractional_utc_stays_blocked_for_replay(self):
        r = audit("2026-11-12T10:00:00.123456Z",
                  "2026-11-12T10:00:01.123456Z", NONCE)
        self.assertEqual(r["status"], "TIME_WINDOW_CLAIMS_CONSISTENT_ONLY")
        self.assertFalse(r["replay_prevented"])
        self.assertFalse(r["order_placement_enabled"])

if __name__ == "__main__":
    unittest.main()
