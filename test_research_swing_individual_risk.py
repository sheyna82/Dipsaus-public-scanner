import unittest
from research_swing_individual_risk import individual_risk_at_close,allocation_fraction

class RiskTests(unittest.TestCase):
    def test_stable(self):
        bars=[{"open":100,"close":100} for _ in range(21)]
        r=individual_risk_at_close(bars,20)
        self.assertEqual(r["risk_band"],"ordinary")
        self.assertFalse(r["event_calendar_verified"])
        self.assertEqual(allocation_fraction(r,"scaled"),1)
    def test_single_crash(self):
        bars=[{"open":100,"close":100} for _ in range(21)]
        bars[20]={"open":88,"close":85}
        r=individual_risk_at_close(bars,20)
        self.assertEqual(r["risk_band"],"extreme")
        self.assertEqual(allocation_fraction(r,"screen"),0)
        self.assertEqual(allocation_fraction(r,"scaled"),0)
    def test_no_lookahead(self):
        bars=[{"open":100,"close":100} for _ in range(21)]
        first=individual_risk_at_close(bars,20)
        bars.append({"open":20,"close":10})
        self.assertEqual(first,individual_risk_at_close(bars,20))
if __name__=="__main__":
    unittest.main()
