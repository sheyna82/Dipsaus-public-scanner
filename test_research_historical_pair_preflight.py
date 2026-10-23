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

    def test_identical_payloads_rejected(self):
        data = payload(0)
        with self.assertRaisesRegex(ValueError, "identical_stock_and_benchmark"):
            prepare_historical_research_pair(
                manifest(data), data, manifest(data), data)


if __name__ == "__main__":
    unittest.main()
