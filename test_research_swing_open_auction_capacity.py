"""Synthetic tests for opening auction participation capacity."""
import unittest
from research_swing_open_auction_capacity import assess_open_auction_capacity


def item(shares=20, volume=10000):
    return {"ticker": "A", "planned_shares": shares,
            "opening_auction_volume": volume}


class AuctionCapacityTests(unittest.TestCase):
    def test_within_one_percent_capacity(self):
        result = assess_open_auction_capacity([item(20, 10000)])
        self.assertTrue(result["results"]["A"]["capacity_screen_passed"])
        self.assertFalse(result["historical_fill_guaranteed"])

    def test_exceeds_one_percent_capacity(self):
        result = assess_open_auction_capacity([item(101, 10000)])
        self.assertFalse(result["results"]["A"]["capacity_screen_passed"])

    def test_round_down_capacity(self):
        result = assess_open_auction_capacity([item(1, 99)])
        self.assertEqual(result["results"]["A"]["max_modeled_shares"], 0)

    def test_missing_auction_volume_rejected(self):
        x = item()
        del x["opening_auction_volume"]
        with self.assertRaisesRegex(ValueError, "invalid_liquidity_input"):
            assess_open_auction_capacity([x])

    def test_fractional_volume_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_opening_auction_volume"):
            assess_open_auction_capacity([item(volume=10.5)])

    def test_invalid_participation_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid_participation_limit"):
            assess_open_auction_capacity([item()], max_participation_pct=0)

    def test_duplicate_ticker_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate_or_invalid"):
            assess_open_auction_capacity([item(), item()])


if __name__ == "__main__":
    unittest.main()
