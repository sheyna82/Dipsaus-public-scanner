import unittest
from portfolio_downside_research import evaluate_intraday_downside as check, replay_intraday

class DownsideTests(unittest.TestCase):
    def test_detect(self):
        c=[100.]*30+[98.5,98.3,98.1,97.9,97.7]
        h=[100.2]*30+[99.0,98.8,98.6,98.4,98.2]
        l=[99.5]*30+[98.4,98.2,98.,97.8,97.6]
        o=[100.]*30+[98.8,98.6,98.4,98.2,98.0]
        self.assertTrue(check(c,h,l,o,enabled=True)['trigger'])
    def test_disabled(self):
        self.assertEqual(check([],[],[],[])['status'],'DISABLED')
    def test_insufficient(self):
        self.assertEqual(check([100],[100],[99],[100],enabled=True)['status'],'INSUFFICIENT_DATA')
    def test_flat(self):
        self.assertFalse(check([100.]*35,[100.2]*35,[99.8]*35,[100.]*35,enabled=True)['trigger'])
    def test_inconsistent_ohlc(self):
        self.assertEqual(check([100.]*35,[99.]*35,[99.]*35,[100.]*35,enabled=True)['status'],'INVALID_OHLC')
    def test_gradual_decline_without_break(self):
        self.assertFalse(check([99.]*35,[100.]*35,[98.]*35,[99.]*35,enabled=True)['trigger'])
    def test_replay_detects_without_future_bars(self):
        rows=[{'open':100.,'high':100.2,'low':99.5,'close':100.} for _ in range(30)]
        for i in range(5):
            rows.append({'open':98.8-i*.2,'high':99.-i*.2,'low':98.4-i*.2,'close':98.5-i*.2})
        result=replay_intraday(rows,enabled=True)
        self.assertEqual(result['first_signal_index'],34)
        self.assertEqual(result['signal_count'],1)
    def test_replay_disabled(self):
        self.assertEqual(replay_intraday([],enabled=False)['status'],'DISABLED')
    def test_replay_missing_field(self):
        self.assertEqual(replay_intraday([{}]*31,enabled=True)['status'],'INVALID_DATA')
    def test_nan(self):
        self.assertEqual(check([float('nan')]*35,[100.]*35,[99.]*35,[100.]*35,enabled=True)['status'],'INVALID_DATA')
if __name__=='__main__':
    unittest.main()
