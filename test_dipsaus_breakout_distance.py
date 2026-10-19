import unittest
from dipsaus_breakout_distance import breakout_distance, message_context


class DistanceTests(unittest.TestCase):
    def row(self, **kw):
        return dict(market="US", provider_quote=kw.get("price", 79.36),
                    route_2_break_above=kw.get("level", 77.0))

    def test_extended_does_not_claim_buy(self):
        r = self.row()
        self.assertEqual(breakout_distance(r)["status"], "EXTENDED")
        self.assertIn("GEEN koopbevestiging", message_context(r))

    def test_near(self):
        self.assertEqual(breakout_distance(self.row(level=79))["status"], "NEAR_BREAKOUT")

    def test_below(self):
        self.assertEqual(breakout_distance(self.row(level=80))["status"], "BELOW_BREAKOUT")

    def test_missing_is_unknown(self):
        r = self.row(); r.pop("route_2_break_above")
        self.assertEqual(breakout_distance(r)["status"], "UNKNOWN")
        self.assertIn("ONBEKEND", message_context(r))

    def test_invalid_numeric_is_unknown(self):
        for bad in (True, float("nan"), 0, -1, "79"):
            self.assertEqual(breakout_distance(self.row(price=bad))["status"], "UNKNOWN")

    def test_eu_untouched(self):
        r = self.row(); r["market"] = "EU"
        self.assertEqual(breakout_distance(r)["status"], "NOT_APPLICABLE")


if __name__ == "__main__":
    unittest.main()
