import unittest
from research_benchmark_source_admission import assess_source, omxh25_yahoo_candidate

class SourceAdmissionTests(unittest.TestCase):
    def test_omxh25_stays_blocked(self):
        result = omxh25_yahoo_candidate()
        self.assertFalse(result["research_calculation_eligible"])
        self.assertEqual(result["unmet_requirements"], [
            "provider_series_mapping_verified", "historical_values_verified",
            "data_use_rights_verified"])
        self.assertFalse(result["trade_ready"])

    def test_missing_or_nonboolean_evidence_rejected(self):
        base = dict(source_id="example", research_only=True, trade_ready=False,
                    official_identity_verified=True, provider_series_mapping_verified=True,
                    historical_values_verified=True, data_use_rights_verified=True)
        for field in ("official_identity_verified", "data_use_rights_verified"):
            with self.subTest(field=field):
                altered = dict(base)
                altered.pop(field)
                with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID_SOURCE_GATE"):
                    assess_source(altered)
                altered[field] = "true"
                with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID_SOURCE_GATE"):
                    assess_source(altered)

    def test_unsafe_trading_state_rejected(self):
        record = dict(source_id="example", research_only=True, trade_ready=True,
                      official_identity_verified=True, provider_series_mapping_verified=True,
                      historical_values_verified=True, data_use_rights_verified=True)
        with self.assertRaisesRegex(ValueError, "UNSAFE_SOURCE_STATE"):
            assess_source(record)

    def test_only_fully_documented_source_admitted_for_research(self):
        record = dict(source_id="licensed-example", research_only=True, trade_ready=False,
                      official_identity_verified=True, provider_series_mapping_verified=True,
                      historical_values_verified=True, data_use_rights_verified=True)
        result = assess_source(record)
        self.assertTrue(result["research_calculation_eligible"])
        self.assertFalse(result["trade_ready"])

if __name__ == "__main__":
    unittest.main()
