import unittest
from research.swing_lifecycle.purged_training_split import partition_training_rows


def row(decision, outcome):
    return {"decision_at": decision, "outcome_available_at": outcome}


class PurgedTrainingSplitTests(unittest.TestCase):
    def test_purge_outcome_crossing_cutoff(self):
        cutoff = "2026-07-01T00:00:00Z"
        eligible, purged, future, invalid = partition_training_rows([
            row("2026-06-20T12:00:00Z", "2026-06-30T23:59:59Z"),
            row("2026-06-25T12:00:00Z", "2026-07-02T00:00:00Z"),
            row("2026-06-25T12:00:00Z", cutoff),
            row(cutoff, "2026-07-05T00:00:00Z"),
            row("2026-06-25T12:00:00", "2026-06-30T00:00:00Z"),
        ], cutoff)
        self.assertEqual([len(x) for x in (eligible, purged, future, invalid)], [1, 2, 1, 1])

    def test_timezone_offsets_compared_in_utc(self):
        eligible, purged, future, invalid = partition_training_rows([
            row("2026-06-30T20:00:00-04:00", "2026-07-01T01:00:00Z"),
            row("2026-06-30T20:00:00+02:00", "2026-06-30T23:00:00Z"),
        ], "2026-07-01T00:00:00Z")
        self.assertEqual([len(x) for x in (eligible, purged, future, invalid)], [1, 0, 1, 0])

    def test_invalid_outcome_before_decision(self):
        eligible, purged, future, invalid = partition_training_rows([
            row("2026-06-20T00:00:00Z", "2026-06-19T00:00:00Z"),
        ], "2026-07-01T00:00:00Z")
        self.assertEqual([len(x) for x in (eligible, purged, future, invalid)], [0, 0, 0, 1])


if __name__ == "__main__":
    unittest.main()
