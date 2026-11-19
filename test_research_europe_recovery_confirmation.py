import unittest
from research_europe_recovery_confirmation import evaluate
H=[{"day":"2026-11-04","stock_close":100,"benchmark_close":100},
   {"day":"2026-11-05","stock_close":102,"benchmark_close":101},
   {"day":"2026-11-06","stock_close":104,"benchmark_close":102}]
class Tests(unittest.TestCase):
    def test_unverified_identity_blocks(self):
        with self.assertRaisesRegex(ValueError,"BENCHMARK_IDENTITY_UNVERIFIED"):
            evaluate(H,"2026-11-06")
    def test_two_positive_sessions_observation_only(self):
        result=evaluate(H,"2026-11-06",True)
        self.assertTrue(result["two_positive_relative_sessions"])
        self.assertEqual(len(result["observations"]),2)
        self.assertEqual(result["observations"][-1]["day"],"2026-11-06")
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["approved_signal"])
    def test_partial_session_excluded(self):
        partial={"day":"2026-11-09","stock_close":1,"benchmark_close":999}
        result=evaluate(H+[partial],"2026-11-06",True)
        self.assertEqual(result["latest_complete_day"],"2026-11-06")
        self.assertTrue(result["two_positive_relative_sessions"])
    def test_missing_sessions_block(self):
        with self.assertRaisesRegex(ValueError,"INSUFFICIENT_COMPLETED_SESSIONS"):
            evaluate(H[:2],"2026-11-06",True)
    def test_duplicate_session_blocks(self):
        with self.assertRaisesRegex(ValueError,"DUPLICATE_DAY"):
            evaluate(H+[H[0]],"2026-11-06",True)
    def test_negative_second_day(self):
        h=[*H[:2],{"day":"2026-11-06","stock_close":101,"benchmark_close":102}]
        self.assertFalse(evaluate(h,"2026-11-06",True)["two_positive_relative_sessions"])
if __name__=="__main__":unittest.main()
