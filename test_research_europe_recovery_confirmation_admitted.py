import unittest
from unittest.mock import patch
from research_europe_recovery_confirmation_admitted import evaluate_admitted
from research_europe_relative_strength_admitted import receipt_digest

def evidence(name="OMXH25", **changes):
    result = dict(source_id=name, official_identity_verified=True,
                  provider_series_mapping_verified=True, historical_values_verified=True,
                  data_use_rights_verified=True, research_only=True, trade_ready=False)
    result.update(changes)
    return result

class RecoveryAdmissionTests(unittest.TestCase):
    def invoke(self, receipt=None, name="OMXH25"):
        return evaluate_admitted([], "2026-11-06", name,
                                evidence() if receipt is None else receipt)

    def test_unpinned_all_true_receipt_blocks_before_evaluate(self):
        with patch("research_europe_recovery_confirmation_admitted.evaluate") as calc:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_RECEIPT_NOT_TRUSTED"):
                self.invoke()
            calc.assert_not_called()

    def test_unverified_rights_blocks_before_evaluate(self):
        with patch("research_europe_recovery_confirmation_admitted.evaluate") as calc:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_NOT_ADMITTED"):
                self.invoke(evidence(data_use_rights_verified=False))
            calc.assert_not_called()

    def test_mismatched_benchmark_blocks(self):
        with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_ID_MISMATCH"):
            self.invoke(name="AEX")

    def test_modified_receipt_blocks_even_if_original_pinned(self):
        original = evidence()
        altered = evidence(review_note="modified")
        with patch("research_europe_relative_strength_admitted.TRUSTED_SOURCE_RECEIPT_SHA256",
                   {"OMXH25": receipt_digest(original)}), patch(
                   "research_europe_recovery_confirmation_admitted.TRUSTED_SOURCE_RECEIPT_SHA256",
                   {"OMXH25": receipt_digest(original)}), patch(
                   "research_europe_recovery_confirmation_admitted.evaluate") as calc:
            with self.assertRaisesRegex(ValueError, "BENCHMARK_SOURCE_RECEIPT_NOT_TRUSTED"):
                self.invoke(altered)
            calc.assert_not_called()

    def test_pinned_fixture_delegates_research_only(self):
        source = evidence()
        with patch("research_europe_recovery_confirmation_admitted.TRUSTED_SOURCE_RECEIPT_SHA256",
                   {"OMXH25": receipt_digest(source)}), patch(
                   "research_europe_recovery_confirmation_admitted.evaluate",
                   return_value={"research_only": True, "trade_ready": False}) as calc:
            result = self.invoke(source)
            calc.assert_called_once_with([], "2026-11-06", benchmark_identity_verified=True)
            self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
