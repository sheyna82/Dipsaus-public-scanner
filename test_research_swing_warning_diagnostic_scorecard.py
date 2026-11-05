import unittest
from research_swing_warning_diagnostic_scorecard import warning_diagnostic_scorecard

class DiagnosticScorecardTests(unittest.TestCase):
    def test_flat_panel_does_not_invent_predictive_evidence(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(60)]
        result=warning_diagnostic_scorecard({"FLAT":rows},horizons=(5,),step=5)
        signal=result["horizons"]["5"]["signals"]["combined"]
        self.assertEqual(signal["alerts"],0)
        self.assertIsNone(signal["false_alarm_fraction"])
        self.assertFalse(signal["late_evidence_sufficient"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["portfolio_net_return_tested"])

    def test_detects_missed_drawdown(self):
        rows=[{"timestamp":i,"open":100,"high":101,"low":99,"close":100} for i in range(60)]
        rows[21]={"timestamp":21,"open":90,"high":91,"low":80,"close":90}
        result=warning_diagnostic_scorecard({"DROP":rows},horizons=(5,),step=5)
        self.assertGreaterEqual(result["horizons"]["5"]["signals"]["combined"]["missed_large_drawdowns"],1)

if __name__=="__main__":
    unittest.main()
