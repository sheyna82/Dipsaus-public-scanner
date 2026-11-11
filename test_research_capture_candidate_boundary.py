import unittest
from research_capture_candidate_boundary import audit_capture_candidate_boundary


class BoundaryTests(unittest.TestCase):
    def manifest(self):
        return {"captured_at_utc": "2026-11-03T14:57:22+00:00",
                "last_common_eligible_session": "2026-11-02",
                "prospective_candidate_registered": False,
                "independent_prospective_proof": False}

    def test_registration_after_capture_with_future_outcomes(self):
        report = audit_capture_candidate_boundary(
            self.manifest(), registered_at_utc="2026-11-03T15:00:00+00:00",
            outcome_sessions=("2026-11-04", "2026-11-05"))
        self.assertTrue(report["capture_precedes_registration"])
        self.assertFalse(report["independent_prospective_proof"])

    def test_backdated_registration_blocked(self):
        with self.assertRaisesRegex(ValueError, "candidate_registered_before_source_capture"):
            audit_capture_candidate_boundary(
                self.manifest(), registered_at_utc="2026-11-02T21:00:00+00:00")

    def test_same_day_outcome_blocked(self):
        with self.assertRaisesRegex(ValueError, "outcome_session_not_after_registration"):
            audit_capture_candidate_boundary(
                self.manifest(), registered_at_utc="2026-11-03T15:00:00+00:00",
                outcome_sessions=("2026-11-03",))

    def test_unverified_proof_claim_blocked(self):
        m = self.manifest()
        m["independent_prospective_proof"] = True
        with self.assertRaisesRegex(ValueError, "unsupported_prospective_proof_claim"):
            audit_capture_candidate_boundary(m, registered_at_utc="2026-11-03T15:00:00+00:00")


if __name__ == "__main__":
    unittest.main()
