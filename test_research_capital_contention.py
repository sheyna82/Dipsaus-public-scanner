import unittest
from research_capital_contention import simulate_capacity_contention as simulate

def candidate(identifier, entry, exit):
    return {"id": identifier, "entry_date": entry, "exit_date": exit}

class CapitalContentionTests(unittest.TestCase):
    def test_cash_blocks_second_overlapping_entry(self):
        result = simulate([
            candidate("A", "2026-01-05", "2026-01-12"),
            candidate("B", "2026-01-06", "2026-01-13")],
            starting_cash_eur=3500)
        self.assertEqual([e["decision"] for e in result["events"]],
                         ["SIMULATED_ACCEPT", "INSUFFICIENT_SIMULATED_CASH"])
        self.assertFalse(result["trade_ready"])

    def test_exit_releases_cash_before_same_day_entry(self):
        result = simulate([
            candidate("A", "2026-01-05", "2026-01-12"),
            candidate("B", "2026-01-12", "2026-01-19")],
            starting_cash_eur=3500)
        self.assertEqual(result["simulated_accept_count"], 2)

    def test_position_cap_applies_with_existing_positions(self):
        result = simulate([
            candidate("A", "2026-01-05", "2026-01-12"),
            candidate("B", "2026-01-06", "2026-01-13")],
            starting_cash_eur=50000, max_positions=3, initial_open_positions=2)
        self.assertEqual(result["events"][1]["decision"], "POSITION_LIMIT")

    def test_registration_order_not_future_performance(self):
        result = simulate([
            candidate("FIRST", "2026-01-05", "2026-01-12"),
            candidate("SECOND", "2026-01-05", "2026-01-13")],
            starting_cash_eur=3500)
        self.assertEqual(result["events"][0]["id"], "FIRST")
        self.assertEqual(result["simulated_accept_count"], 1)

    def test_invalid_dates_and_duplicates_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_DATES"):
            simulate([candidate("A", "2026-01-10", "2026-01-05")], starting_cash_eur=3500)
        with self.assertRaisesRegex(ValueError, "INVALID_CANDIDATE_ID"):
            simulate([candidate("A", "2026-01-05", "2026-01-12"),
                      candidate("A", "2026-01-06", "2026-01-13")], starting_cash_eur=3500)

    def test_zero_cash_never_accepts(self):
        result = simulate([candidate("A", "2026-01-05", "2026-01-12")],
                          starting_cash_eur=0)
        self.assertEqual(result["simulated_accept_count"], 0)

if __name__ == "__main__":
    unittest.main()
