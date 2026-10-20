import unittest
from notification_delivery_audit import audit_delivery_state

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
