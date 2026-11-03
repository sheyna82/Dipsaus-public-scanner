import unittest
from research.candidate_exante_priority_sensitivity import score_from_signal_close, compare_priorities


class ExAntePriorityTests(unittest.TestCase):
    def setUp(self):
        self.thresholds = {"relative_strength_20d_pct": 0, "volume_ratio_20d": 1,
                           "atr_14_pct": 3}
        self.features = {"status": "DESCRIPTIVE_ONLY", "relative_strength_20d_pct": 1,
                         "volume_ratio_20d": 2, "atr_14_pct": 2}

    def test_score_directions(self):
        self.assertGreater(score_from_signal_close(self.features, self.thresholds), 0)

    def test_future_return_not_used_for_ranking(self):
        rows = []
        for symbol, outcome in (("AAA", -10), ("ZZZ", 10)):
            rows.append({"symbol": symbol, "entry_day": 21000, "exit_day": 21010,
                         "features_at_signal_close": dict(self.features),
                         "training_thresholds": self.thresholds,
                         "historical_net_return_pct_outcome_not_selection_input": outcome})
        first = compare_priorities(rows)
        rows[0]["historical_net_return_pct_outcome_not_selection_input"] = 20
        second = compare_priorities(rows)
        self.assertEqual(first["priority"]["score_desc"]["accepted_n"],
                         second["priority"]["score_desc"]["accepted_n"])
        self.assertFalse(first["future_outcomes_used_for_priority"])

    def test_capacity_priority_selects_preentry_high_score(self):
        rows = []
        for i in range(7):
            features = dict(self.features)
            features["relative_strength_20d_pct"] = 10 if i == 6 else 0
            rows.append({"symbol": f"S{i:02d}", "entry_day": 21000,
                         "exit_day": 21010,
                         "features_at_signal_close": features,
                         "training_thresholds": self.thresholds,
                         "historical_net_return_pct_outcome_not_selection_input": 10 if i == 6 else 0})
        result = compare_priorities(rows)
        self.assertEqual(result["event_count"], 7)
        self.assertEqual(result["priority"]["score_desc"]["accepted_n"], 6)
        self.assertEqual(result["priority"]["score_desc"]["realized_pnl"], 350.0)
        self.assertEqual(result["priority"]["symbol_asc"]["realized_pnl"], 0.0)

    def test_outcome_swap_does_not_change_selection(self):
        rows = []
        for i in range(7):
            features = dict(self.features)
            features["relative_strength_20d_pct"] = float(i)
            rows.append({"symbol": f"S{i:02d}", "entry_day": 21000,
                         "exit_day": 21010, "features_at_signal_close": features,
                         "training_thresholds": self.thresholds,
                         "historical_net_return_pct_outcome_not_selection_input": 0.0})
        rows[0]["historical_net_return_pct_outcome_not_selection_input"] = 10.0
        first = compare_priorities(rows)
        rows[0]["historical_net_return_pct_outcome_not_selection_input"] = 0.0
        rows[6]["historical_net_return_pct_outcome_not_selection_input"] = 10.0
        second = compare_priorities(rows)
        # Score prefers S06 regardless of where the future winner is placed.
        self.assertEqual(first["priority"]["score_desc"]["realized_pnl"], 0.0)
        self.assertEqual(second["priority"]["score_desc"]["realized_pnl"], 350.0)
        self.assertEqual(first["priority"]["score_desc"]["accepted_n"], 6)
        self.assertEqual(second["priority"]["score_desc"]["accepted_n"], 6)

    def test_missing_feature_fails_closed(self):
        features = dict(self.features)
        del features["volume_ratio_20d"]
        with self.assertRaises(ValueError):
            score_from_signal_close(features, self.thresholds)

    def test_invalid_feature_status_fails_closed(self):
        with self.assertRaises(ValueError):
            score_from_signal_close({"status": "INSUFFICIENT_LOOKBACK"}, self.thresholds)

    def test_duplicate_event_rejected(self):
        row = {"symbol": "AAA", "entry_day": 21000, "exit_day": 21010,
               "features_at_signal_close": self.features,
               "training_thresholds": self.thresholds,
               "historical_net_return_pct_outcome_not_selection_input": 5}
        with self.assertRaises(ValueError):
            compare_priorities([row, row])


if __name__ == "__main__":
    unittest.main()
