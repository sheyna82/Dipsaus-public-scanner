import unittest
from datetime import date
from research_swing_walkforward_splits import Fold
from research_swing_walkforward_selection import select_walkforward_candidate


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.fold = Fold(date(2020,1,1),date(2020,12,1),
                         date(2021,1,1),date(2021,3,1),20)

    def test_select_training_only(self):
        rows = [
            dict(decision_date=date(2020,6,1),exit_date=date(2020,6,8),candidate="A",net_return_pct=2),
            dict(decision_date=date(2020,6,1),exit_date=date(2020,6,8),candidate="B",net_return_pct=1),
            dict(decision_date=date(2021,1,4),exit_date=date(2021,1,11),candidate="A",net_return_pct=-8),
            dict(decision_date=date(2021,1,4),exit_date=date(2021,1,11),candidate="B",net_return_pct=99),
        ]
        result = select_walkforward_candidate(rows,[self.fold],min_train_trades=1)[0]
        self.assertEqual(result["chosen_candidate"],"A")
        self.assertEqual(result["validation_mean_net_pct"],-8)

    def test_purge_training_label_crossing_boundary(self):
        rows=[dict(decision_date=date(2020,11,30),exit_date=date(2021,1,2),
                   candidate="A",net_return_pct=999)]
        result=select_walkforward_candidate(rows,[self.fold],min_train_trades=1)[0]
        self.assertIsNone(result["chosen_candidate"])

    def test_reject_future_validation_exit(self):
        rows=[dict(decision_date=date(2020,6,1),exit_date=date(2020,6,2),
                   candidate="A",net_return_pct=1),
              dict(decision_date=date(2021,2,28),exit_date=date(2021,3,3),
                   candidate="A",net_return_pct=100)]
        result=select_walkforward_candidate(rows,[self.fold],min_train_trades=1)[0]
        self.assertEqual(result["validation_trades"],0)

    def test_reject_invalid_rows(self):
        with self.assertRaises(ValueError):
            select_walkforward_candidate([dict(decision_date=date(2020,1,1),
               exit_date=date(2020,1,2),candidate="A",net_return_pct=float("nan"))],
               [self.fold])


if __name__=="__main__":
    unittest.main()
