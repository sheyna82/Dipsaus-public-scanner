import unittest
from unittest.mock import patch
from research_europe_relative_strength_admitted import compare_admitted

REQUIRED = ("AEX", "DAX_PRICE", "OMXH25", "STOXX600_PRICE")

def receipt(name, **overrides):
    value = dict(source_id=name, research_only=True, trade_ready=False,
                 official_identity_verified=True, provider_series_mapping_verified=True,
                 historical_values_verified=True, data_use_rights_verified=True)
    value.update(overrides)
    return value

class AdmissionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.receipts = {name: receipt(name) for name in REQUIRED}

    def invoke(self, receipts):
        return compare_admitted({}, {}, {}, "2026-11-06", receipts)

    def test_missing_benchmark_receipt_rejected_before_computation(self):
        records = dict(self.receipts)
        del records["OMXH25"]
        with patch("research_europe_relative_strength_admitted.compare") as calculate:
            with self.assertRaisesRegex(ValueError, "INCOMPLETE_BENCHMARK_SOURCE_RECEIPTS"):
                self.invoke(records)
            calculate.assert_not_called()

    def test_unresolved_yahoo_mapping_blocks_calculation(self):
        records = dict(self.receipts)
        records["OMXH25"] = receipt("OMXH25", provider_series_mapping_verified=False)
        with patch("research_europe_relative_strength_admitted.compare") as calculate:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_NOT_ADMITTED:OMXH25"):
                self.invoke(records)
            calculate.assert_not_called()

    def test_unverified_rights_block_calculation(self):
        records = dict(self.receipts)
        records["AEX"] = receipt("AEX", data_use_rights_verified=False)
        with patch("research_europe_relative_strength_admitted.compare") as calculate:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_NOT_ADMITTED:AEX"):
                self.invoke(records)
            calculate.assert_not_called()

    def test_source_id_mismatch_rejected(self):
        records = dict(self.receipts)
        records["DAX_PRICE"] = receipt("other")
        with patch("research_europe_relative_strength_admitted.compare") as calculate:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_ID_MISMATCH"):
                self.invoke(records)
            calculate.assert_not_called()

    def test_admitted_sources_delegate_to_existing_calculator(self):
        with patch("research_europe_relative_strength_admitted.compare",
                   return_value={"research_only": True, "trade_ready": False}) as calculate:
            result = self.invoke(self.receipts)
            calculate.assert_called_once_with({}, {}, {}, "2026-11-06")
            self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
