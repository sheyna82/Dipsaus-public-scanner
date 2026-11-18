"""Synthetic normalized aggregates and supplied completion receipts."""
import unittest
from research.us_aggregate_forward_bridge_20261118 import bridge_normalized_bars

def snap():
    return {"status":"WATCH_UNVERIFIED","snapshot":{
        "symbol":"SYNTH","historical_friction_usd":100,
        "historical_close_usd":99,"source_last_bar_utc":"2026-11-17T20:00:00Z",
        "decision_observed_utc":"2026-11-17T21:00:00Z"}}

def data():
    return {"status":"NORMALIZED_UNVERIFIED","provider_id":"massive",
            "bars":[{"time":"2026-11-17T22:00:00Z","close":101}]}

def receipts():
    return [{"source_bar_start_utc":"2026-11-17T22:00:00Z",
             "bar_end_utc":"2026-11-17T22:59:00Z",
             "observed_utc":"2026-11-17T23:00:00Z"}]

class AggregateBridgeTests(unittest.TestCase):
    def test_completed_bar_passes_to_replay(self):
        x=bridge_normalized_bars(snap(),data(),receipts())
        self.assertEqual(x["pattern_status"],"BREAKOUT_OBSERVED")
        self.assertFalse(x["trade_ready"])

    def test_missing_receipts_block(self):
        self.assertEqual(bridge_normalized_bars(snap(),data(),[])["status"],"BLOCKED")

    def test_start_not_end(self):
        r=receipts();r[0]["bar_end_utc"]=r[0]["source_bar_start_utc"]
        self.assertEqual(bridge_normalized_bars(snap(),data(),r)["status"],"BLOCKED")

    def test_end_after_observation(self):
        r=receipts();r[0]["observed_utc"]="2026-11-17T22:30:00Z"
        self.assertEqual(bridge_normalized_bars(snap(),data(),r)["status"],"BLOCKED")

    def test_wrong_start_binding(self):
        r=receipts();r[0]["source_bar_start_utc"]="2026-11-17T21:00:00Z"
        self.assertEqual(bridge_normalized_bars(snap(),data(),r)["status"],"BLOCKED")

    def test_unverified_normalization(self):
        d=data();d["status"]="UNKNOWN"
        self.assertEqual(bridge_normalized_bars(snap(),d,receipts())["status"],"BLOCKED")

    def test_wrong_provider(self):
        d=data();d["provider_id"]="unknown"
        self.assertEqual(bridge_normalized_bars(snap(),d,receipts())["status"],"BLOCKED")

    def test_naive_receipt(self):
        r=receipts();r[0]["observed_utc"]="2026-11-17T23:00:00"
        self.assertEqual(bridge_normalized_bars(snap(),data(),r)["status"],"BLOCKED")

    def test_no_source_authentication_claim(self):
        x=bridge_normalized_bars(snap(),data(),receipts())
        self.assertIn("RECEIPT_INDEPENDENCE_NOT_ATTESTED",x["blocks"])
        self.assertFalse(x["order_placement_enabled"])

    def test_missing_snapshot(self):
        self.assertEqual(bridge_normalized_bars(None,data(),receipts())["status"],"BLOCKED")

if __name__=="__main__":
    unittest.main()
