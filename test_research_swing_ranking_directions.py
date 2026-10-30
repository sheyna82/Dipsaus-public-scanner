"""Small manually checkable ranking-direction tests."""
import unittest
from research_swing_ranking_directions import RANKING_DIRECTIONS, rank_candidates


class RankingDirectionsTests(unittest.TestCase):
    def test_every_method_has_expected_direction(self):
        self.assertEqual(len(RANKING_DIRECTIONS), 18)
        scores = [("B", 2.0), ("A", 1.0), ("C", 3.0)]
        for method, direction in RANKING_DIRECTIONS.items():
            with self.subTest(method=method):
                ranked = rank_candidates(scores, method)
                self.assertEqual([x[0] for x in ranked],
                                 ["C", "B", "A"] if direction == "descending"
                                 else ["A", "B", "C"])

    def test_ma20_variants_are_opposites(self):
        distances = [("NEAR", 0.01), ("FAR", 0.15), ("MID", 0.05)]
        self.assertEqual(rank_candidates(distances, "closest_to_ma20")[0][0], "NEAR")
        self.assertEqual(rank_candidates(distances, "farthest_from_ma20")[0][0], "FAR")

    def test_ties_are_deterministic(self):
        self.assertEqual(rank_candidates([("Z", 1), ("A", 1)], "closest_to_ma20"),
                         [("A", 1), ("Z", 1)])

    def test_invalid_inputs(self):
        for rows in [[("A", float("nan"))], [("A", float("inf"))],
                     [("A", 1), ("A", 2)], [("", 1)]]:
            with self.assertRaises(ValueError):
                rank_candidates(rows, "deepest_dip")
        with self.assertRaises(ValueError):
            rank_candidates([], "unknown")


if __name__ == "__main__":
    unittest.main()
