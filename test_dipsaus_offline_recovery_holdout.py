import unittest
from datetime import date, timedelta
from dipsaus_offline_recovery_holdout import chronological_holdout


def sample(i, signal_day, final_day):
    return {"id": str(i), "signal_time": signal_day + "T16:00:00+00:00",
            "bars": [{"date": signal_day}, {"date": final_day}]}


class HoldoutTests(unittest.TestCase):
    def test_chronological_partition_and_embargo(self):
        rows = [sample(i, f"2026-10-{i:02d}", f"2026-10-{i+1:02d}")
                for i in range(1, 9)]
        r = chronological_holdout(rows, embargo_sessions=1)
        self.assertEqual([x["id"] for x in r["holdout"]], ["7", "8"])
        self.assertEqual([x["id"] for x in r["development"]], ["1", "2", "3", "4", "5"])
        self.assertIn("6", r["purged_ids"])

    def test_overlapping_outcome_purged(self):
        rows = [sample(i, f"2026-10-{i:02d}", f"2026-10-{i+1:02d}")
                for i in range(1, 9)]
        rows[3]["bars"][-1]["date"] = "2026-10-08"
        r = chronological_holdout(rows, embargo_sessions=0)
        self.assertIn("4", r["purged_ids"])

    def test_tied_timestamp_kept_in_same_partition(self):
        rows = [sample(i, "2026-10-01" if i < 4 else "2026-10-02",
                       "2026-10-03") for i in range(1, 7)]
        r = chronological_holdout(rows, embargo_sessions=0)
        self.assertEqual(len(r["holdout"]), 3)
        self.assertEqual(len(r["development"]), 0)
        self.assertEqual(len(r["purged_ids"]), 3)

    def test_rejects_bad_input(self):
        rows = [sample(i, f"2026-10-{i:02d}", f"2026-10-{i+1:02d}")
                for i in range(1, 5)]
        self.assertIsNone(chronological_holdout(rows[:3]))
        self.assertIsNone(chronological_holdout(rows, holdout_fraction=1.0))
        rows[1]["id"] = "1"
        self.assertIsNone(chronological_holdout(rows))


if __name__ == "__main__":
    unittest.main()
