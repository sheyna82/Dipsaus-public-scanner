import unittest
from research_batch_manifest import reconcile_batch_manifest as reconcile

M = {"batch_id": "synthetic-batch", "started_utc": "2026-01-01T00:00:00Z",
     "completed_utc": "2026-01-01T01:00:00Z", "expected_signal_count": 2,
     "expected_decision_counts": {"SELECTED": 1, "REJECTED": 1, "DEFERRED": 0}}
def signal(i, decision):
    return {"schema_version": 1, "event_id": format(i, "032x"),
            "candidate_id": format(i+100, "032x"),
            "observed_utc": "2026-01-01T00:30:00Z",
            "event_type": "SIGNAL", "source_digest": "b"*64,
            "feature_digest": "c"*64, "decision": decision}
E = [signal(1, "SELECTED"), signal(2, "REJECTED")]

class BatchManifestTests(unittest.TestCase):
    def test_matching_counts_do_not_prove_universe(self):
        r = reconcile(M, E)
        self.assertEqual(r["status"], "BATCH_COUNTS_MATCH_SELF_REPORTED")
        self.assertTrue(r["count_match"])
        self.assertFalse(r["complete_candidate_universe_verified"])
        self.assertFalse(r["manifest_independently_attested"])

    def test_missing_rejected_signal_detected(self):
        r = reconcile(M, E[:1])
        self.assertEqual(r["status"], "BATCH_COUNT_MISMATCH")
        self.assertEqual(r["observed_decision_counts"]["REJECTED"], 0)

    def test_equal_total_but_wrong_disposition_detected(self):
        r = reconcile(M, [E[0], signal(2, "DEFERRED")])
        self.assertEqual(r["status"], "BATCH_COUNT_MISMATCH")

    def test_inconsistent_declared_total_blocked(self):
        r = reconcile({**M, "expected_signal_count": 3}, E)
        self.assertEqual(r["reason"], "INVALID_DECLARED_COUNTS")

    def test_negative_count_blocked(self):
        r = reconcile({**M, "expected_decision_counts":
                       {"SELECTED": -1, "REJECTED": 1, "DEFERRED": 0}}, E)
        self.assertEqual(r["reason"], "INVALID_DECLARED_COUNTS")

    def test_outside_window_blocked(self):
        r = reconcile(M, [{**E[0], "observed_utc": "2026-01-02T00:00:00Z"}, E[1]])
        self.assertEqual(r["reason"], "SIGNAL_OUTSIDE_BATCH_WINDOW")

    def test_duplicate_event_blocked(self):
        self.assertEqual(reconcile(M, [E[0], E[0]])["reason"],
                         "INVALID_EVENT_CONTRACT")

    def test_invalid_manifest_field_blocked(self):
        self.assertEqual(reconcile({**M, "ticker": "secret"}, E)["reason"],
                         "INVALID_MANIFEST")

if __name__ == "__main__":
    unittest.main()
