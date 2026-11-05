"""Offline no-lookahead checks for pre-entry features."""
import unittest
from candidate_preentry_features import pre_entry_features

def series(n=45):
    return [{"timestamp":1700000000+i*86400,"open":100+i,
             "close":100+i,"high":101+i,"low":99+i,
             "volume":1000+i*10} for i in range(n)]

class FeatureTests(unittest.TestCase):
    def test_future_mutation_does_not_change_features(self):
        stock=series()
        benchmark=series()
        before=pre_entry_features(stock,benchmark,30)
        self.assertEqual(before["status"],"DESCRIPTIVE_ONLY")
        for row in stock[31:]:
            row.update(close=100000,high=100001,low=99999,volume=999999)
        for row in benchmark[31:]:
            row["close"]=100000
        self.assertEqual(before,pre_entry_features(stock,benchmark,30))

    def test_insufficient_history_blocks(self):
        self.assertEqual(pre_entry_features(series(),series(),10)["status"],"INSUFFICIENT_LOOKBACK")

    def test_missing_benchmark_blocks(self):
        self.assertEqual(pre_entry_features(series(),[],30)["status"],"BENCHMARK_ALIGNMENT_BLOCKED")

if __name__=="__main__":unittest.main()
