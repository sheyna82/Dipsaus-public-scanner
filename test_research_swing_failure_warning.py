import unittest
from research_swing_failure_warning import failure_warning_at_close

class FailureWarningTests(unittest.TestCase):
    def test_no_warning_flat(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(21)]
        self.assertFalse(failure_warning_at_close(bars,20)["warning"])
    def test_breakdown(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(21)]
        bars[20]={"open":99,"high":100,"low":90,"close":91}
        r=failure_warning_at_close(bars,20)
        self.assertTrue(r["warning"])
        self.assertTrue(r["breakdown"])
    def test_future_is_not_used(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(21)]
        result=failure_warning_at_close(bars,20)
        bars.append({"open":50,"high":51,"low":49,"close":50})
        self.assertEqual(result,failure_warning_at_close(bars,20))
    def test_bad_ohlc_rejected(self):
        bars=[{"open":100,"high":101,"low":99,"close":100} for _ in range(21)]
        bars[20]["low"]=105
        with self.assertRaisesRegex(ValueError,"inconsistent_ohlc"):
            failure_warning_at_close(bars,20)
if __name__=="__main__":
    unittest.main()
