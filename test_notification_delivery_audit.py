import unittest
from notification_delivery_audit import audit_delivery_state, format_public_delivery_summary, audit_delivery_delta

class DeliveryAuditTests(unittest.TestCase):
    def test_distinguishes_provider_acceptance_from_phone_receipt(self):
        result=audit_delivery_state({"signals":{"one":{"delivery":"sent"}}})
        self.assertEqual(result["sent_to_provider"],1)
        self.assertFalse(result["phone_receipt_verified"])
        self.assertFalse(result["delivery_verified"])

    def test_failure_states_are_not_delivered(self):
        result=audit_delivery_state({"signals":{
            "a":{"delivery":"reserved"},"b":{"delivery":"rejected"},
            "c":{"delivery":"uncertain"},"d":{}}})
        self.assertEqual(result["sent_to_provider"],0)
        self.assertEqual(result["reserved"],1)
        self.assertEqual(result["rejected"],1)
        self.assertEqual(result["uncertain"],1)
        self.assertEqual(result["unknown"],1)

    def test_missing_state_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_delivery_state({})

    def test_public_summary_contains_only_aggregate_counters(self):
        result=format_public_delivery_summary({"signals":{
            "SECRET_TICKER":{"delivery":"sent"}}})
        self.assertIn("sent_to_provider=1",result)
        self.assertIn("phone_receipt_verified=false",result)
        self.assertNotIn("SECRET_TICKER",result)

    def test_delta_excludes_unchanged_historical_sends(self):
        before={"signals":{"old":{"delivery":"sent"}}}
        after={"signals":{"old":{"delivery":"sent"},
                          "new":{"delivery":"rejected"}}}
        result=audit_delivery_delta(before,after)
        self.assertEqual(result["records"],1)
        self.assertEqual(result["sent_to_provider"],0)
        self.assertEqual(result["rejected"],1)
        self.assertEqual(result["scope"],"changed_records_not_confirmed_attempts")
