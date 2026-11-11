"""Tests for fail-closed signal chain provenance research."""
import unittest
from research_scanner_signal_chain_provenance_gate import audit_signal_chain


class SignalChainTests(unittest.TestCase):
    def base(self):
        return {
            "signal_id": "research-001", "symbol": "TEST", "family": "EARLY_RECOVERY",
            "decision_utc": "2026-10-26T13:00:00Z",
            "generated_utc": "2026-10-26T13:01:00Z",
            "provider_accepted_utc": "2026-10-26T13:02:00Z",
            "entry_utc": "2026-10-27T14:30:00Z",
            "decision_source_verified": True,
            "signal_rule_version_verified": True,
            "point_in_time_inputs_verified": True,
            "market_data_source_verified": True,
            "execution_verified": True,
            "costs_and_currency_verified": True,
            "phone_receipt_verified": False,
        }

    def test_complete_evidence_separates_phone_receipt(self):
        result = audit_signal_chain([self.base()])
        self.assertEqual(result["reconstructable_signals"], 1)
        self.assertEqual(result["reconstructable_trades"], 1)
        self.assertFalse(result["records"][0]["phone_receipt_verified"])

    def test_missing_provenance_rejected(self):
        row = self.base()
        row["point_in_time_inputs_verified"] = False
        self.assertEqual(audit_signal_chain([row])["reconstructable_signals"], 0)

    def test_no_execution_is_not_a_trade(self):
        row = self.base()
        row["execution_verified"] = False
        result = audit_signal_chain([row])
        self.assertEqual(result["reconstructable_signals"], 1)
        self.assertEqual(result["reconstructable_trades"], 0)

    def test_out_of_order_event_rejected(self):
        row = self.base()
        row["generated_utc"] = "2026-10-26T12:00:00Z"
        self.assertEqual(audit_signal_chain([row])["reconstructable_signals"], 0)

    def test_duplicate_identity_rejected(self):
        row = self.base()
        with self.assertRaisesRegex(ValueError, "duplicate_signal_id"):
            audit_signal_chain([row, row])

    def test_naive_timestamp_rejected(self):
        row = self.base()
        row["decision_utc"] = "2026-10-26T13:00:00"
        self.assertEqual(audit_signal_chain([row])["reconstructable_signals"], 0)


    def test_provider_before_generation_rejected(self):
        row = self.base()
        row["provider_accepted_utc"] = "2026-10-26T12:59:00Z"
        result = audit_signal_chain([row])
        self.assertEqual(result["reconstructable_signals"], 0)
        self.assertEqual(result["reconstructable_trades"], 0)

    def test_entry_before_decision_rejected(self):
        row = self.base()
        row["entry_utc"] = "2026-10-26T12:59:00Z"
        result = audit_signal_chain([row])
        self.assertEqual(result["reconstructable_signals"], 0)
        self.assertEqual(result["reconstructable_trades"], 0)


if __name__ == "__main__":
    unittest.main()
