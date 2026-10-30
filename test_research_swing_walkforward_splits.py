import unittest
from datetime import date, timedelta
from research_swing_walkforward_splits import walk_forward_folds, check_disjoint


class WalkForwardTests(unittest.TestCase):
    def setUp(self):
        self.dates = [date(2020, 1, 1) + timedelta(days=i) for i in range(1000)]

    def test_expanding_nonoverlapping(self):
        folds = walk_forward_folds(self.dates, min_train_sessions=400,
                                   validation_sessions=100, embargo_sessions=20,
                                   step_sessions=100)
        self.assertEqual(len(folds), 5)
        self.assertTrue(check_disjoint(folds))
        self.assertEqual(folds[0].train_end, self.dates[399])
        self.assertEqual(folds[0].validation_start, self.dates[420])
        self.assertEqual(folds[1].train_end, self.dates[499])

    def test_no_data(self):
        self.assertEqual(walk_forward_folds([], min_train_sessions=2), [])

    def test_reject_unsorted_or_duplicate(self):
        with self.assertRaises(ValueError):
            walk_forward_folds([self.dates[1], self.dates[0]])
        with self.assertRaises(ValueError):
            walk_forward_folds([self.dates[0], self.dates[0]])

    def test_reject_invalid_lengths(self):
        with self.assertRaises(ValueError):
            walk_forward_folds(self.dates, embargo_sessions=-1)
        with self.assertRaises(ValueError):
            walk_forward_folds(self.dates, step_sessions=0)


if __name__ == "__main__":
    unittest.main()
