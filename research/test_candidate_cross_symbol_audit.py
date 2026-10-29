"""Offline invariants for cross-symbol breadth reporting."""
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from candidate_cross_symbol_audit import audit

def sample(symbol,signal_n,control_n,median,status="INSUFFICIENT_MATCHED_CONTROLS"):
    evaluation={"signal_n":signal_n,"matched_control_n":control_n,
                "risk_screen_50bps":{"status":status},
                "cost_scenarios":{"50":{"next_open_signals":{"median_net_pct":median}}}}
    return {"symbol":symbol,"patterns":{
        "breakout_prior20":{"10":evaluation},
        "recovery_from_prior20_low_3to15pct":{"10":evaluation}}}

class CrossSymbolAuditTests(unittest.TestCase):
    def test_unmatched_controls_are_explicit(self):
        data={"candidates":[sample("AAA",40,10,2),sample("BBB",20,5,-1)]}
        result=audit(data)
        p=result["patterns"]["breakout_prior20"]
        self.assertEqual(p["total_nonoverlap_within_symbol_signals"],60)
        self.assertEqual(p["signals_without_matching_controls"],45)
        self.assertEqual(p["symbols_with_at_least_30_signals"],1)
        self.assertEqual(p["symbols_with_at_least_15_controls"],0)
        self.assertFalse(result["trade_ready"])
    def test_blocked_symbols_excluded_not_hidden(self):
        result=audit({"candidates":[sample("AAA",30,20,1),
                                    {"symbol":"BAD","status":"DATA_BLOCKED"}]})
        self.assertEqual(result["data_blocked"],["BAD"])
        self.assertEqual(result["patterns"]["breakout_prior20"]["symbols_evaluated"],1)

if __name__=="__main__":unittest.main()
