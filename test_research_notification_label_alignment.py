import unittest
from research_notification_signal_cases import CASES_2026_10_26
from research_notification_label_alignment import label_alignment
class AlignmentTests(unittest.TestCase):
    def test_flags_early_recovery_near_high_without_error_claim(self):
        r=label_alignment(CASES_2026_10_26,[{"symbol":"VIST","stage":"MOMENTUM_NEAR_HIGH"},{"symbol":"FANG","stage":"MOMENTUM_NEAR_HIGH"}])
        flags=[x["symbol"] for x in r if x["review_early_recovery_label"]]
        self.assertEqual(flags,["VIST","FANG"])
        self.assertTrue(all(not x["alert_error_proven"] for x in r))
if __name__=="__main__":unittest.main()
