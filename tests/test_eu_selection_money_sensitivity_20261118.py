import unittest
from research.eu_selection_money_sensitivity_20261118 import required_gross_move as calc

class MoneySensitivityTests(unittest.TestCase):
    def test_zero_friction(self):
        r=calc(allocation_eur="3500")
        self.assertEqual(r["required_gross_move_pct"],"4.29")
        self.assertFalse(r["trade_ready"])
    def test_illustrative_fixed_fees(self):
        r=calc(allocation_eur="3500",round_trip_fixed_eur="9.80")
        self.assertEqual(r["required_gross_profit_eur"],"159.80")
        self.assertEqual(r["required_gross_move_pct"],"4.57")
    def test_illustrative_variable_friction(self):
        r=calc(allocation_eur="3500",round_trip_variable_pct="0.25")
        self.assertEqual(r["assumed_round_trip_friction_eur"],"8.75")
        self.assertEqual(r["required_gross_move_pct"],"4.54")
    def test_combined_friction(self):
        r=calc(allocation_eur="3500",round_trip_fixed_eur="9.80",round_trip_variable_pct="0.25")
        self.assertEqual(r["required_gross_move_pct"],"4.82")
    def test_invalid_zero_allocation(self):
        self.assertEqual(calc(allocation_eur="0")["status"],"BLOCKED")
    def test_boolean_rejected(self):
        self.assertEqual(calc(allocation_eur=True)["status"],"BLOCKED")
    def test_negative_friction_rejected(self):
        self.assertEqual(calc(allocation_eur="3500",round_trip_fixed_eur="-1")["status"],"BLOCKED")
    def test_no_trade_permission_even_with_zero_friction(self):
        r=calc(allocation_eur="3500")
        self.assertFalse(r["notify"])
        self.assertFalse(r["automatic_orders"])
if __name__=="__main__":
    unittest.main()
