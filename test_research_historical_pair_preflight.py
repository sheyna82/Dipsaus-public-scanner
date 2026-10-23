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
        benchmark = payload(10).replace(b"2025-01-03", b"2025-02-03").replace(
            b"2025-01-03", b"2025-02-03")
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["shared_price_dates"], 0)
        self.assertTrue(result["no_overlapping_price_dates"])
        self.assertFalse(result["all_shared_close_values_match"])

    def test_partial_overlap_is_reported_asymmetric(self):
        stock = payload(0)
        benchmark = payload(10).replace(b"2025-01-02", b"2025-02-02")
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
        self.assertFalse(result["benchmark_independence_verified"])

    def test_distinct_returns_do_not_match(self):
        stock, benchmark = payload(0), payload(10)
        result = prepare_historical_research_pair(
            manifest(stock), stock, manifest(benchmark), benchmark)
        self.assertEqual(result["comparable_shared_return_intervals"], 1)
        self.assertEqual(result["matching_shared_return_intervals"], 0)
        self.assertFalse(result["all_comparable_shared_returns_match"])

    def test_identical_payloads_rejected(self):
        data = payload(0)
        with self.assertRaisesRegex(ValueError, "identical_stock_and_benchmark"):
            prepare_historical_research_pair(
                manifest(data), data, manifest(data), data)


if __name__ == "__main__":
    unittest.main()
