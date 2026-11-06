"""Date-granular capital-ledger regression tests."""
import unittest
from integrated_overlapping_capital_ledger import simulate

def t(i, start="2026-11-02", end="2026-11-10", allocation=3500):
    return {"id": str(i), "entry_date": start, "exit_date": end,
            "allocation_eur": allocation, "research_only": True, "trade_ready": False}

class OverlapLedgerTests(unittest.TestCase):
    def test_non_overlapping_cash_reuse(self):
        result = simulate([t("A", end="2026-11-05", allocation=50000),
                           t("B", start="2026-11-05", allocation=50000)])
        self.assertEqual(result["accepted_ids"], ["A", "B"])
        self.assertEqual(result["rejected"], [])
        self.assertFalse(result["trade_ready"])

    def test_overlapping_cash_shortage(self):
        result = simulate([t("A", allocation=30000), t("B", allocation=30000)])
        self.assertEqual(len(result["accepted_ids"]), 1)
        self.assertEqual(result["rejected"][0]["reason"], "INSUFFICIENT_CASH")

    def test_six_position_limit(self):
        result = simulate([t(str(i), allocation=1000) for i in range(7)])
        self.assertEqual(len(result["accepted_ids"]), 6)
        self.assertEqual(result["rejected"][0]["reason"], "MAX_POSITIONS")

    def test_cash_released_on_exit(self):
        result = simulate([t("A", end="2026-11-05", allocation=3500),
                           t("B", start="2026-11-05", end="2026-11-12", allocation=3500)])
        self.assertEqual(result["ending_free_cash_eur"], "46500")

    def test_duplicate_id_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_ID"):
            simulate([t("A"), t("A")])

    def test_invalid_date_order_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_DATE_ORDER"):
            simulate([t("A", start="2026-11-10", end="2026-11-02")])

    def test_negative_allocation_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_MONEY"):
            simulate([t("A", allocation=-1)])

    def test_unsafe_trade_blocks(self):
        item = t("A")
        item["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "NOT_RESEARCH_ONLY"):
            simulate([item])

    def test_nonfinite_capital_blocks(self):
        with self.assertRaisesRegex(ValueError, "INVALID_MONEY"):
            simulate([], capital_eur="NaN")

    def test_no_trades(self):
        result = simulate([])
        self.assertEqual(result["ending_free_cash_eur"], "50000")
        self.assertFalse(result["portfolio_validated"])

if __name__ == "__main__":
    unittest.main()
