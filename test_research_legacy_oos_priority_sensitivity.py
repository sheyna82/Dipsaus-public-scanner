import unittest
from datetime import date
from research_legacy_oos_priority_sensitivity import compare_legacy_oos_same_day_priority

def day(iso):
    return (date.fromisoformat(iso) - date(1970, 1, 1)).days

class PrioritySensitivityTests(unittest.TestCase):
    def rows(self):
        return [{"symbol": s, "entry_day": day("2026-10-01"),
                 "exit_day": day("2026-10-15"), "net_return_pct": r}
                for s, r in (("AMD", 1), ("META", 2), ("TSLA", -1))]

    def compare(self, rows=None, **kwargs):
        return compare_legacy_oos_same_day_priority(
            self.rows() if rows is None else rows,
            b"synthetic frozen fixture", source_name="fixture",
            retrieved_at_utc="2026-11-05T12:00:00Z",
            starting_settled_cash_eur=3500,
            tranches_eur=(3500,), **kwargs)

    def test_competing_same_day_candidates_change_identity_not_count(self):
        r = self.compare()
        s = r["sensitivity"][0]
        self.assertTrue(s["same_day_priority_changes_accepted_candidates"])
        self.assertEqual(s["accepted_count_range"], [1, 1])
        self.assertEqual(s["symbol_asc"]["accepted_candidate_ids"], ["AMD:" + str(day("2026-10-01"))])
        self.assertEqual(s["symbol_desc"]["accepted_candidate_ids"], ["TSLA:" + str(day("2026-10-01"))])
        self.assertFalse(r["trade_ready"])

    def test_mismatched_fee_assumption_is_blocked(self):
        with self.assertRaisesRegex(ValueError, "LEGACY_SIMULATOR_COST_MODEL_MISMATCH"):
            self.compare(simulator_round_trip_cost_rate=.01)

if __name__ == "__main__":
    unittest.main()
