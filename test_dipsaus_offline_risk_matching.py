import unittest
from dipsaus_offline_risk_matching import match_risk_controls


def record(id, sector="energy", regime="down", atr=3):
    return {"id": id, "sector": sector, "market_regime": regime, "atr_pct": atr}


class RiskMatchingTests(unittest.TestCase):
    def test_match_sector_regime_and_atr(self):
        warnings = [record("w1"), record("w2", atr=3.5)]
        controls = [record("c1", atr=3.1), record("c2", atr=3.6),
                    record("c3", sector="tech", atr=3)]
        r = match_risk_controls(warnings, controls)
        self.assertEqual([(p["warning_id"], p["control_id"]) for p in r["pairs"]],
                         [("w1", "c1"), ("w2", "c2")])
        self.assertEqual(r["matched_share_pct"], 100)
        self.assertIsNone(r["order_instruction"])

    def test_no_cross_regime_match(self):
        r = match_risk_controls([record("w")], [record("c", regime="up")])
        self.assertEqual(r["matched_warnings"], 0)
        self.assertEqual(r["unmatched_warning_ids"], ["w"])

    def test_no_control_reuse(self):
        r = match_risk_controls([record("w1"), record("w2")], [record("c")])
        self.assertEqual(r["matched_warnings"], 1)

    def test_reject_duplicate_ids_and_invalid_atr(self):
        self.assertIsNone(match_risk_controls([record("same")], [record("same")]))
        self.assertIsNone(match_risk_controls([record("w", atr=float("nan"))], []))


if __name__ == "__main__":
    unittest.main()
