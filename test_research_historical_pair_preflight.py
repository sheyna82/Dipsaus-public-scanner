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
        self.assertFalse(result["benchmark_independence_verified"])
        self.assertFalse(result["research_data_ready"])
        self.assertFalse(result["trade_ready"])

    def test_identical_payloads_rejected(self):
        data = payload(0)
        with self.assertRaisesRegex(ValueError, "identical_stock_and_benchmark"):
            prepare_historical_research_pair(
                manifest(data), data, manifest(data), data)


if __name__ == "__main__":
    unittest.main()
