import unittest

from research_observation_temporal_integrity import audit_observation_timing


class TemporalIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "signal_session": "2026-11-02",
            "source_observed_at_utc": "2026-11-03T15:00:00Z",
            "registered_at_utc": "2026-11-03T16:00:00+00:00",
            "research_only": True, "trade_ready": False, "future_outcome": None,
            "registration_clock_proof_independent": False,
            "independent_source_authentication": False,
        }

    def test_late_registration_explicitly_non_prospective(self):
        result = audit_observation_timing(self.record)
        self.assertEqual(result["status"], "late_registration_not_prospective_for_signal_session")
        self.assertFalse(result["prospective_signal_proven"])

    def test_same_day_does_not_claim_proof(self):
        self.record["signal_session"] = "2026-11-03"
        result = audit_observation_timing(self.record)
        self.assertEqual(result["status"], "same_day_registration_requires_exchange_cutoff_proof")
        self.assertFalse(result["independent_pre_signal_timestamp_proof"])

    def test_observation_after_registration_rejected(self):
        self.record["source_observed_at_utc"] = "2026-11-03T17:00:00Z"
        with self.assertRaisesRegex(ValueError, "observation_after_registration"):
            audit_observation_timing(self.record)

    def test_naive_registration_rejected(self):
        self.record["registered_at_utc"] = "2026-11-03T16:00:00"
        with self.assertRaisesRegex(ValueError, "registration_time_not_utc"):
            audit_observation_timing(self.record)

    def test_claimed_independent_clock_rejected(self):
        self.record["registration_clock_proof_independent"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_registration_clock_proof"):
            audit_observation_timing(self.record)


if __name__ == "__main__":
    unittest.main()
