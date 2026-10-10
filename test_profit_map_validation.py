import unittest
from profit_map_validation import zone, assess


class ProfitMapTests(unittest.TestCase):
    def test_no_cross_currency_fallback(self):
        self.assertIsNone(zone({'first_decision_zone_usd': [10, 11]}, 'EUR', 'first_friction', 'first_decision_zone'))

    def test_eur_and_legacy_usd_zones(self):
        self.assertEqual(zone({'profit_map': {'first_friction_eur': [10, 11]}}, 'EUR', 'first_friction'), [10, 11])
        self.assertEqual(zone({'first_decision_zone_usd': [10, 11]}, 'USD', 'first_friction', 'first_decision_zone'), [10, 11])

    def test_invalid_zones(self):
        for value in ([11, 10], [True, 12], [float('nan'), 12], [-1, 12], [10]):
            self.assertIsNone(zone({'first_friction_eur': value}, 'EUR', 'first_friction'))

    def test_completeness_requires_euro_profit_and_order(self):
        mapping = {'first_friction_eur': [10, 11], 'first_meaningful_resistance_eur': [12, 13], 'further_recovery_zone_eur': [14, 15]}
        item = {'profit_map': mapping}
        self.assertEqual(assess(item, 'EUR')['status'], 'INCOMPLETE')
        mapping['gross_profit_eur_at_zones'] = {name: 150 for name in ('first_friction', 'first_meaningful_resistance', 'further_recovery_zone')}
        self.assertEqual(assess(item, 'EUR')['status'], 'COMPLETE')
        mapping['further_recovery_zone_eur'] = [9, 10]
        self.assertIn('ordered_recovery_zones', assess(item, 'EUR')['missing'])
