"""Focused integration regressions for held-out portfolio comparison (research only)."""
import unittest
from unittest.mock import patch
from candidate_feature_oos import portfolio_oos_pair

def rows(n=800, offset=0):
    return [{"timestamp":1700000000+(i+offset)*86400,
             "open":100.0,"close":100.0,"high":101.0,"low":99.0,"volume":1000}
            for i in range(n)]

class PortfolioOOSPairTests(unittest.TestCase):
    def test_empty_universe_returns_no_trades(self):
        result=portfolio_oos_pair({}, [], "recovery")
        self.assertEqual(result["baseline"]["accepted_n"],0)
        self.assertEqual(result["filtered"]["accepted_n"],0)
        self.assertFalse(result["trade_ready"])

    def test_insufficient_history_is_excluded(self):
        result=portfolio_oos_pair({"ABC":rows(20)}, [], "recovery")
        self.assertEqual(result["excluded_symbols"]["ABC"],"INSUFFICIENT_HISTORY")
        self.assertEqual(result["baseline"]["accepted_n"],0)

    def test_filter_only_removes_baseline_events_and_thresholds_use_training(self):
        stock=rows()
        calls=[]
        def mock_features(data,i):
            return {"recovery":i in (100,600,620)}
        def mock_preentry(data,benchmark,i):
            calls.append(i)
            return {"index":i}
        def mock_fit(training):
            self.assertEqual([i for i,_ in training],[100])
            return {"status":"TRAINING_ONLY_THRESHOLDS","thresholds":{"trained_on":100}}
        def mock_label(f, fitted):
            self.assertEqual(fitted["thresholds"]["trained_on"],100)
            return {"status":"RESEARCH_ONLY","passes":{"feature":f["index"]==600}}
        with patch("candidate_feature_oos.features",side_effect=mock_features), \
             patch("candidate_feature_oos.pre_entry_features",side_effect=mock_preentry), \
             patch("candidate_feature_oos.training_median_thresholds",side_effect=mock_fit), \
             patch("candidate_feature_oos.label",side_effect=mock_label):
            result=portfolio_oos_pair({"ABC":stock}, [], "recovery")
        self.assertEqual(result["baseline"]["accepted_n"],2)
        self.assertEqual(result["filtered"]["accepted_n"],1)
        self.assertEqual(result["filtered"]["accepted_signals"][0]["entry_day"],
                         stock[601]["timestamp"]//86400)
        self.assertAlmostEqual(result["baseline"]["realized_pnl"],-35.0)
        self.assertTrue(all(i<520 or i in (600,620) for i in calls))
        self.assertFalse(result["daily_mark_to_market_verified"])

    def test_common_calendar_start_excludes_early_held_out_signals(self):
        early=rows(800)
        late=rows(800,offset=50)
        def mock_features(data,i):
            return {"recovery":i in (100,550,600)}
        with patch("candidate_feature_oos.features",side_effect=mock_features), \
             patch("candidate_feature_oos.pre_entry_features",return_value={"feature":1}), \
             patch("candidate_feature_oos.training_median_thresholds",
                   return_value={"status":"TRAINING_ONLY_THRESHOLDS","thresholds":{}}), \
             patch("candidate_feature_oos.label",
                   return_value={"status":"RESEARCH_ONLY","passes":{"feature":True}}):
            result=portfolio_oos_pair({"EARLY":early,"LATE":late}, [], "recovery")
        start=result["common_test_start_day"]
        self.assertEqual(start,late[521]["timestamp"]//86400)
        self.assertTrue(all(t["entry_day"]>=start
                            for t in result["baseline"]["accepted_signals"]))
        self.assertEqual(result["baseline"]["accepted_n"],2)

    def test_common_end_excludes_trades_exiting_after_shortest_history(self):
        short=rows(750)
        long=rows(850)
        def mock_features(data,i):
            return {"recovery":i in (100,600,760)}
        with patch("candidate_feature_oos.features",side_effect=mock_features), \
             patch("candidate_feature_oos.pre_entry_features",return_value={"feature":1}), \
             patch("candidate_feature_oos.training_median_thresholds",
                   return_value={"status":"TRAINING_ONLY_THRESHOLDS","thresholds":{}}), \
             patch("candidate_feature_oos.label",
                   return_value={"status":"RESEARCH_ONLY","passes":{"feature":True}}):
            result=portfolio_oos_pair({"SHORT":short,"LONG":long}, [], "recovery")
        self.assertEqual(result["common_test_end_day"],short[-1]["timestamp"]//86400)
        self.assertTrue(all(t["exit_day"]<=result["common_test_end_day"]
                            for t in result["baseline"]["accepted_signals"]))

    def test_multiple_symbols_share_capacity_and_do_not_reuse_same_day_proceeds(self):
        stock=rows()
        symbols={f"S{i:02d}":stock for i in range(7)}
        def mock_features(data,i):
            return {"recovery":i in (100,600)}
        with patch("candidate_feature_oos.features",side_effect=mock_features), \
             patch("candidate_feature_oos.pre_entry_features",return_value={"feature":1}), \
             patch("candidate_feature_oos.training_median_thresholds",
                   return_value={"status":"TRAINING_ONLY_THRESHOLDS","thresholds":{}}), \
             patch("candidate_feature_oos.label",
                   return_value={"status":"RESEARCH_ONLY","passes":{"feature":True}}):
            result=portfolio_oos_pair(symbols, [], "recovery")
        self.assertEqual(result["baseline"]["accepted_n"],6)
        self.assertEqual(result["baseline"]["rejection_reasons"]["CAPACITY_FULL"],1)
        self.assertEqual(result["filtered"]["accepted_n"],6)

if __name__=="__main__":
    unittest.main()
