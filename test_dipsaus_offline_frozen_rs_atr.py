import unittest
from datetime import date, timedelta
from dipsaus_offline_frozen_rs_atr import annotate_frozen_events_rs_atr


def bars(growth=0.4, n=90):
    result = []
    for i in range(n):
        close = 100 + growth * i
        result.append({"date": (date(2025, 1, 1) + timedelta(days=i)).isoformat(),
                       "open": close, "high": close + 1, "low": close - 1,
                       "close": close, "volume": 1000})
    return result


class FrozenRSATRTests(unittest.TestCase):
    def test_causal_features_present_and_not_trade_ready(self):
        r = annotate_frozen_events_rs_atr(bars(), bars(0.2))
        self.assertEqual(r["status"], "EXPLORATORY_FROZEN_RS_ATR")
        self.assertGreater(r["events"], 0)
        self.assertTrue(all(x["relative_strength_20d_pct_points"] > 0 for x in r["rows"]))
        self.assertTrue(all(x["atr_14d_pct"] > 0 for x in r["rows"]))
        self.assertFalse(r["trade_ready"])

    def test_future_changes_do_not_modify_earlier_features(self):
        stock, spy = bars(), bars(0.2)
        a = annotate_frozen_events_rs_atr(stock, spy)
        stock[-1]["high"] *= 1.8
        stock[-1]["close"] *= 1.5
        b = annotate_frozen_events_rs_atr(stock, spy)
        self.assertEqual(a["rows"][0]["relative_strength_20d_pct_points"],
                         b["rows"][0]["relative_strength_20d_pct_points"])
        self.assertEqual(a["rows"][0]["atr_14d_pct"], b["rows"][0]["atr_14d_pct"])

    def test_unaligned_dates_are_blocked(self):
        spy = bars(0.2)
        spy[30]["date"] = "2025-01-31"
        self.assertEqual(annotate_frozen_events_rs_atr(bars(), spy)["status"], "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
