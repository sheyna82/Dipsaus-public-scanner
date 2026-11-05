import unittest
from dipsaus_offline_matched_downside import matched_downside as compare


def bars(low=95):
    return [{"date": "2025-01-%02d" % (i + 1), "open": 100, "low": low} for i in range(20)]


class MatchedDownsideTests(unittest.TestCase):
    def test_adverse_excursion_vs_market(self):
        r = compare(bars(90), bars(97), [0], horizon=10)
        self.assertEqual(r["status"], "EXPLORATORY_MATCHED_DOWNSIDE")
        self.assertEqual(r["rows"][0]["stock_adverse_pct"], -10)
        self.assertEqual(r["rows"][0]["benchmark_adverse_pct"], -3)
        self.assertEqual(r["mean_extra_adverse_pct_points"], -7)
        self.assertFalse(r["trade_ready"])

    def test_no_drawdown_when_all_lows_above_entry(self):
        r = compare(bars(101), bars(101), [0])
        self.assertEqual(r["rows"][0]["stock_adverse_pct"], 0)

    def test_overlap_rejected(self):
        self.assertEqual(compare(bars(), bars(), [0, 2])["reason"], "overlap_or_invalid_index")

    def test_misalignment_rejected(self):
        a, b = bars(), bars()
        b[1]["date"] = "2025-02-02"
        self.assertEqual(compare(a, b, [0])["reason"], "unaligned_sessions")

    def test_bad_low_rejected(self):
        a, b = bars(), bars()
        a[2]["low"] = -1
        self.assertEqual(compare(a, b, [0])["reason"], "invalid_price")


if __name__ == "__main__":
    unittest.main()
