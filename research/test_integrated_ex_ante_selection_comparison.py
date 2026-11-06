"""Tests for deterministic ex-ante portfolio selection scenarios."""
import unittest
from integrated_ex_ante_selection_comparison import compare_orders

def c(i, priority, allocation=30000):
    return {"id": i, "entry_date": "2026-11-02", "exit_date": "2026-11-10",
            "allocation_eur": allocation, "research_only": True, "trade_ready": False,
            "registered_priority": priority, "priority_source_verified": True,
            "priority_registered_before_entry": True}

class SelectionComparisonTests(unittest.TestCase):
    def test_registered_priority_changes_allocation(self):
        result = compare_orders([c("A", 1), c("B", 3)])
        self.assertEqual(result["baseline"]["accepted_ids"], ["A"])
        self.assertEqual(result["priority"]["accepted_ids"], ["B"])
        self.assertFalse(result["trade_ready"])
        self.assertFalse(result["performance_superiority_proven"])

    def test_unregistered_priority_blocks(self):
        item = c("A", 1)
        item["priority_registered_before_entry"] = False
        with self.assertRaisesRegex(ValueError, "LOOKAHEAD_PRIORITY_BLOCKED"):
            compare_orders([item])

    def test_unverified_source_blocks(self):
        item = c("A", 1)
        item["priority_source_verified"] = False
        with self.assertRaisesRegex(ValueError, "MISSING_EX_ANTE_PRIORITY"):
            compare_orders([item])

    def test_future_pnl_blocks(self):
        item = c("A", 1)
        item["realized_pnl_eur"] = 100
        with self.assertRaisesRegex(ValueError, "FUTURE_OUTCOME_IN_SELECTION"):
            compare_orders([item])

    def test_future_return_blocks(self):
        item = c("A", 1)
        item["future_return"] = 0.1
        with self.assertRaisesRegex(ValueError, "FUTURE_OUTCOME_IN_SELECTION"):
            compare_orders([item])

    def test_duplicate_candidate_blocks(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE"):
            compare_orders([c("A", 1), c("A", 2)])

    def test_deterministic_tie_break(self):
        result = compare_orders([c("B", 1), c("A", 1)])
        self.assertEqual(result["priority"]["accepted_ids"], ["A"])

    def test_empty_candidate_list(self):
        result = compare_orders([])
        self.assertEqual(result["baseline"]["accepted_ids"], [])

if __name__ == "__main__":
    unittest.main()
