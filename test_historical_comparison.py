"""Research-only historical comparison regression tests."""
import unittest
from historical_replay import replay

class ComparisonTests(unittest.TestCase):
    def test_non_eur_is_blocked(self):
        self.assertEqual(replay([], currency='USD')['status'], 'FX-BLOCKED')

if __name__ == '__main__':
    unittest.main()
