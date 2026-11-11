import unittest
from research_swing_dynamic_exit_comparison import compare_exit_policies

class TestExit(unittest.TestCase):
    def test_fixed_and_dynamic(self):
        o=[100]*55
        c=[100]*55
        for i in range(2,55):
            c[i]=110 if i<8 else 98
        r=compare_exit_policies(o,c,horizons=(3,5,10),max_hold=12)
        self.assertEqual(r["fixed"]["3"]["holding_sessions"],3)
        self.assertEqual(r["dynamic"]["exit_index"],9)
        self.assertEqual(r["dynamic"]["reason"],"trailing_close_drawdown_next_open")

    def test_future_data_insufficient(self):
        with self.assertRaises(ValueError):
            compare_exit_policies([100]*5,[100]*5)

    def test_no_same_close_fill(self):
        o=[100]*50
        c=[100]*50
        c[5]=120
        c[6]=90
        r=compare_exit_policies(o,c,horizons=(3,),max_hold=12)
        self.assertEqual(r["dynamic"]["exit_index"],7)

if __name__=="__main__":
    unittest.main()
