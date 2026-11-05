import unittest
from dipsaus_offline_notification_funnel import audit_funnel


class NotificationFunnelTests(unittest.TestCase):
    def test_missing_device_evidence_never_passes(self):
        report = audit_funnel({"EU": {"examined": 20, "eligible": 4,
                                       "attempted": 2, "accepted_by_provider": 2}})
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertFalse(report["notification_delivery_proven"])

    def test_count_inversion_blocks(self):
        stages = {"examined": 5, "eligible": 6, "attempted": 1,
                  "accepted_by_provider": 1, "device_confirmed": 0}
        report = audit_funnel({"EU": stages, "US": stages})
        self.assertEqual(report["status"], "DATA_BLOCKED")

    def test_provider_acceptance_is_not_device_receipt(self):
        row = {"examined": 20, "eligible": 5, "attempted": 3,
               "accepted_by_provider": 2, "device_confirmed": 0}
        report = audit_funnel({"EU": row, "US": row})
        self.assertEqual(report["status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(report["markets"]["EU"]["provider_accepted_not_device_confirmed"], 2)
        self.assertFalse(report["markets"]["EU"]["device_delivery_verified"])
        self.assertFalse(report["notification_delivery_proven"])


if __name__ == "__main__":
    unittest.main()
