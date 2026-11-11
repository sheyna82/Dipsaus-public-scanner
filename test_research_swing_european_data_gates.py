import unittest
from research_swing_european_data_gates import validate_daily_rows,aligned_dates,require_corporate_action_review
def row(t):return {"timestamp":t,"open":10,"high":11,"low":9,"close":10.5}
class TestEuropeanDataGates(unittest.TestCase):
 def test_order(self):
  self.assertEqual(len(validate_daily_rows([row(1729510000),row(1729596400)])),2)
  with self.assertRaises(ValueError):validate_daily_rows([row(1729596400),row(1729510000)])
 def test_misalignment(self):
  with self.assertRaises(ValueError):aligned_dates({"A":[row(1729510000)],"B":[row(1729596400)]})
 def test_actions_not_assumed(self):
  with self.assertRaises(ValueError):require_corporate_action_review({})
  self.assertTrue(require_corporate_action_review({"split_audit":True,"dividend_audit":True}))
if __name__=="__main__":unittest.main()
