"""Synthetic-only tests for stock/benchmark historical preflight."""
import hashlib
import unittest
from research_historical_pair_preflight import prepare_historical_research_pair


def payload(offset):
    return ("date,open,high,low,close,volume\n"
            f"2025-01-02,{100+offset},{101+offset},{99+offset},{100+offset},100\n"
            f"2025-01-03,{101+offset},{102+offset},{100+offset},{101+offset},100\n").encode()


def manifest(data):
    return {
        "provider": "synthetic_fixture", "dataset": "synthetic",
        "source_url": "https://example.invalid/offline",
        "license_reference": "synthetic-only",
        "retrieved_at": "2026-10-23T12:00:00+00:00",
        "sha256": hashlib.sha256(data).hexdigest(),
        "adjustment_policy": "unadjusted",
        "universe_policy": "synthetic",
    }


class HistoricalPairPreflightTests(unittest.TestCase):
    def test_distinct_valid_structural_inputs_do_not_claim_provenance(self):
        stock, benchmark = payload(0), payload(10)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertTrue(result["distinct_payloads"])
        self.assertTrue(result["same_declared_provider"])
        self.assertEqual(result["shared_price_dates"], 2)
        self.assertEqual(result["matching_close_values_on_shared_dates"], 0)
        self.assertFalse(result["all_shared_close_values_match"])
        self.assertTrue(result["same_declared_source_url"])
        self.assertFalse(result["provider_claims_authenticated"])
        self.assertFalse(result["benchmark_independence_verified"])
        self.assertFalse(result["research_data_ready"])
        self.assertFalse(result["trade_ready"])


    def test_different_declared_providers_are_not_verified_independent(self):
        stock, benchmark = payload(0), payload(10)
        benchmark_manifest = manifest(benchmark)
        benchmark_manifest["provider"] = "another_synthetic_provider"
        benchmark_manifest["source_url"] = "https://other.example.invalid/offline"
        result = prepare_historical_research_pair(
            manifest(stock), stock, benchmark_manifest, benchmark)
        self.assertFalse(result["same_declared_provider"])
        self.assertFalse(result["same_declared_source_url"])
        self.assertTrue(result["provider_claims_independence"])
        self.assertFalse(result["distinct_providers_verified"])
        self.assertFalse(result["benchmark_independence_verified"])


    def test_different_payloads_with_identical_closes_are_flagged(self):
        stock = payload(0)
        benchmark = stock.replace(b",100\n", b",200\n")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertTrue(result["all_shared_close_values_match"])
        self.assertEqual(result["matching_close_values_on_shared_dates"], 2)
        self.assertFalse(result["benchmark_independence_verified"])


    def test_numeric_close_formatting_does_not_hide_matches(self):
        stock = payload(0)
        benchmark = stock.replace(b",100,100\n", b",100.00,200\n")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["matching_close_values_on_shared_dates"], 2)
        self.assertTrue(result["all_shared_close_values_match"])

    def test_disjoint_dates_do_not_count_as_matching(self):
        stock = payload(0)
        benchmark = payload(10).replace(b"2025-01-02", b"2025-02-02").replace(
            b"2025-01-03", b"2025-02-03")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["shared_price_dates"], 0)
        self.assertTrue(result["no_overlapping_price_dates"])
        self.assertFalse(result["all_shared_close_values_match"])

    def test_partial_overlap_is_reported_asymmetric(self):
        stock = payload(0)
        benchmark = payload(10).replace(b"2025-01-03", b"2025-02-03")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["shared_price_dates"], 1)
        self.assertEqual(result["stock_only_price_dates"], 1)
        self.assertEqual(result["benchmark_only_price_dates"], 1)
        self.assertEqual(result["stock_date_overlap_fraction"], 0.5)
        self.assertEqual(result["benchmark_date_overlap_fraction"], 0.5)
        self.assertTrue(result["partial_price_date_overlap"])
        self.assertFalse(result["benchmark_independence_verified"])

    def test_disjoint_calendar_has_zero_overlap_fractions(self):
        stock = payload(0)
        benchmark = payload(10).replace(b"2025-01-02", b"2025-02-02").replace(
            b"2025-01-03", b"2025-02-03")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["stock_date_overlap_fraction"], 0)
        self.assertEqual(result["benchmark_date_overlap_fraction"], 0)
        self.assertFalse(result["partial_price_date_overlap"])

    def test_scaled_closes_have_matching_returns(self):
        stock = payload(0)
        benchmark = ("date,open,high,low,close,volume\n"
                     "2025-01-02,200,202,198,200,100\n"
                     "2025-01-03,202,204,200,202,100\n").encode()
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertFalse(result["all_shared_close_values_match"])
        self.assertEqual(result["comparable_shared_return_intervals"], 1)
        self.assertEqual(result["matching_shared_return_intervals"], 1)
        self.assertTrue(result["all_comparable_shared_returns_match"])
        self.assertFalse(result["return_pattern_screening_match"])
        self.assertTrue(result["insufficient_return_overlap"])
        self.assertFalse(result["benchmark_independence_verified"])

    def test_distinct_returns_do_not_match(self):
        stock, benchmark = payload(0), payload(10)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 1)
        self.assertEqual(result["matching_shared_return_intervals"], 0)
        self.assertFalse(result["all_comparable_shared_returns_match"])

    def test_short_return_history_is_explicitly_insufficient(self):
        stock, benchmark = payload(0), payload(10)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 1)
        self.assertEqual(result["minimum_comparable_return_intervals"], 20)
        self.assertFalse(result["return_overlap_sufficient_for_screening"])
        self.assertTrue(result["insufficient_return_overlap"])
        self.assertFalse(result["return_pattern_screening_match"])
        self.assertFalse(result["research_data_ready"])

    def test_long_scaled_series_passes_diagnostic_only(self):
        dates = [f"2025-01-{day:02d}" for day in range(1, 23)]
        def series(scale):
            lines = ["date,open,high,low,close,volume"]
            for index, date in enumerate(dates):
                close = (100 + index) * scale
                lines.append(f"{date},{close},{close+scale},{close-scale},{close},100")
            return ("\n".join(lines) + "\n").encode()
        stock, benchmark = series(1), series(2)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 21)
        self.assertEqual(result["matching_shared_return_intervals"], 21)
        self.assertTrue(result["return_overlap_sufficient_for_screening"])
        self.assertTrue(result["return_pattern_screening_match"])
        self.assertFalse(result["all_shared_close_values_match"])
        self.assertFalse(result["benchmark_independence_verified"])
        self.assertFalse(result["trade_ready"])

    def test_partial_return_match_fraction(self):
        stock = ("date,open,high,low,close,volume\n"
                 "2025-01-02,100,101,99,100,100\n"
                 "2025-01-03,101,102,100,101,100\n"
                 "2025-01-04,102,103,101,102,100\n").encode()
        benchmark = ("date,open,high,low,close,volume\n"
                     "2025-01-02,200,201,199,200,100\n"
                     "2025-01-03,202,203,201,202,100\n"
                     "2025-01-04,205,206,204,205,100\n").encode()
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 2)
        self.assertEqual(result["matching_shared_return_intervals"], 1)
        self.assertEqual(result["matching_shared_return_fraction"], 0.5)
        self.assertFalse(result["return_pattern_screening_match"])

    def test_disjoint_dates_have_undefined_return_match_fraction(self):
        stock = payload(0)
        benchmark = payload(10).replace(b"2025-01-02", b"2025-02-02").replace(
            b"2025-01-03", b"2025-02-03")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertIsNone(result["matching_shared_return_fraction"])
        self.assertIsNone(result["comparable_interval_coverage_fraction"])
        self.assertFalse(result["return_pattern_screening_match"])

    def test_nonadjacent_shared_dates_do_not_form_returns(self):
        stock = ("date,open,high,low,close,volume\n"
                 "2025-01-02,100,101,99,100,100\n"
                 "2025-01-03,101,102,100,101,100\n"
                 "2025-01-04,102,103,101,102,100\n").encode()
        benchmark = ("date,open,high,low,close,volume\n"
                     "2025-01-02,200,201,199,200,100\n"
                     "2025-01-04,204,205,203,204,100\n").encode()
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["shared_price_dates"], 2)
        self.assertEqual(result["comparable_shared_return_intervals"], 0)
        self.assertEqual(result["skipped_nonadjacent_shared_intervals"], 1)
        self.assertEqual(result["possible_shared_return_intervals"], 1)
        self.assertEqual(result["comparable_interval_coverage_fraction"], 0.0)
        self.assertIsNone(result["matching_shared_return_fraction"])
        self.assertFalse(result["return_pattern_screening_match"])

    def test_missing_session_in_both_series_preserves_adjacency(self):
        stock = ("date,open,high,low,close,volume\n"
                 "2025-01-02,100,101,99,100,100\n"
                 "2025-01-04,102,103,101,102,100\n").encode()
        benchmark = ("date,open,high,low,close,volume\n"
                     "2025-01-02,200,201,199,200,100\n"
                     "2025-01-04,204,205,203,204,100\n").encode()
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 1)
        self.assertEqual(result["skipped_nonadjacent_shared_intervals"], 0)
        self.assertEqual(result["comparable_interval_coverage_fraction"], 1.0)
        self.assertEqual(result["matching_shared_return_fraction"], 1.0)
        self.assertFalse(result["return_pattern_screening_match"])

    def test_low_coverage_blocks_matching_pattern_screening(self):
        def series(days, scale):
            lines = ["date,open,high,low,close,volume"]
            for day in days:
                close = (100 + day) * scale
                lines.append(f"2025-01-{day:02d},{close},{close+scale},{close-scale},{close},100")
            return ("\n".join(lines) + "\n").encode()
        stock = series(range(1, 32), 1)
        benchmark = series([day for day in range(1, 32) if day % 2], 2)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 0)
        self.assertEqual(result["comparable_interval_coverage_fraction"], 0.0)
        self.assertFalse(result["return_coverage_sufficient_for_screening"])
        self.assertFalse(result["return_pattern_screening_match"])

    def test_many_matching_returns_with_low_coverage_are_blocked(self):
        from datetime import date, timedelta

        start = date(2025, 1, 1)
        def series(indices, scale):
            lines = ["date,open,high,low,close,volume"]
            for index in indices:
                day = (start + timedelta(days=index)).isoformat()
                close = (100 + index) * scale
                lines.append(f"{day},{close},{close+scale},{close-scale},{close},100")
            return ("\n".join(lines) + "\n").encode()

        # Twenty-two shared sessions in a row, then one extra stock-only
        # session before each subsequent shared session.
        shared = list(range(22)) + list(range(24, 64, 2))
        stock_only = [index for index in range(23, 64, 2)]
        stock = series(sorted(shared + stock_only), 1)
        benchmark = series(shared, 2)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 21)
        self.assertEqual(result["matching_shared_return_intervals"], 21)
        self.assertTrue(result["return_overlap_sufficient_for_screening"])
        self.assertLess(result["comparable_interval_coverage_fraction"], 0.8)
        self.assertFalse(result["return_coverage_sufficient_for_screening"])
        self.assertTrue(result["all_comparable_shared_returns_match"])
        self.assertFalse(result["return_pattern_screening_match"])
        self.assertFalse(result["trade_ready"])

    def test_coverage_threshold_boundary_with_long_matching_returns(self):
        from datetime import date, timedelta

        start = date(2025, 1, 1)
        def payload(indices, multiplier):
            lines = ["date,open,high,low,close,volume"]
            for index in sorted(indices):
                close = (100 + index) * multiplier
                day = (start + timedelta(days=index)).isoformat()
                lines.append(f"{day},{close},{close+multiplier},{close-multiplier},{close},100")
            return ("\n".join(lines) + "\n").encode()

        # 26 shared sessions yield 25 possible intervals. The stock
        # has an additional session in selected gaps; benchmark does not.
        shared = list(range(0, 52, 2))
        for skipped_gaps, expected_pass in ((4, True), (5, True), (6, False)):
            extra = [shared[index] + 1 for index in range(0, skipped_gaps * 3, 3)]
            stock = payload(shared + extra, 1)
            benchmark = payload(shared, 2)
            result = prepare_historical_research_pair(
                manifest(stock), stock, manifest(benchmark), benchmark)
            expected_coverage = (25 - skipped_gaps) / 25
            self.assertAlmostEqual(
                result["comparable_interval_coverage_fraction"],
                expected_coverage)
            self.assertEqual(
                result["comparable_shared_return_intervals"], 25 - skipped_gaps)
            self.assertTrue(result["all_comparable_shared_returns_match"])
            self.assertEqual(
                result["return_coverage_sufficient_for_screening"],
                expected_pass)
            self.assertEqual(result["return_pattern_screening_match"],
                             expected_pass)

    def test_clustered_and_scattered_missing_intervals_are_distinguished(self):
        from datetime import date, timedelta

        origin = date(2025, 1, 1)
        def payload(indices, multiplier):
            lines = ["date,open,high,low,close,volume"]
            for index in sorted(indices):
                day = (origin + timedelta(days=2 * index)).isoformat()
                close = (100 + index) * multiplier
                lines.append(f"{day},{close},{close+multiplier},{close-multiplier},{close},100")
            return ("\n".join(lines) + "\n").encode()

        shared = list(range(12))
        benchmark = payload(shared, 2)
        for gap_indices, expected_longest, expected_runs in (
            ([2, 3, 4], 3, 1),
            ([2, 5, 8], 1, 3),
        ):
            # Stock-only observations between adjacent shared dates.
            lines = ["date,open,high,low,close,volume"]
            for index in shared:
                day = (origin + timedelta(days=2 * index)).isoformat()
                close = 100 + index
                lines.append(f"{day},{close},{close+1},{close-1},{close},100")
                if index in gap_indices:
                    gap_day = (origin + timedelta(days=2 * index + 1)).isoformat()
                    lines.append(f"{gap_day},{close},{close+1},{close-1},{close},100")
            stock = ("\n".join(lines) + "\n").encode()
            result = prepare_historical_research_pair(
                manifest(stock), stock, manifest(benchmark), benchmark)
            self.assertEqual(result["skipped_nonadjacent_shared_intervals"], 3)
            self.assertEqual(result["longest_nonadjacent_shared_interval_run"],
                             expected_longest)
            self.assertEqual(result["nonadjacent_shared_interval_run_count"],
                             expected_runs)
            self.assertFalse(result["trade_ready"])

    def test_identical_payloads_rejected(self):
        data = payload(0)
        with self.assertRaisesRegex(ValueError, "identical_stock_and_benchmark"):
            prepare_historical_research_pair(
                manifest(data), data, manifest(data), data)


if __name__ == "__main__":
    unittest.main()
