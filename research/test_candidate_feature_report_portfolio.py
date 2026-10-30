"""Check report entrypoint actually publishes paired portfolio results (offline)."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from candidate_feature_oos import main


class PortfolioReportTests(unittest.TestCase):
    def test_main_writes_both_portfolio_patterns_without_new_downloads(self):
        sample=[{"timestamp":1700000000+i*86400,"open":100.0,
                 "high":101.0,"low":99.0,"close":100.0,"volume":1000}
                for i in range(800)]
        with tempfile.TemporaryDirectory() as folder:
            with patch("candidate_feature_oos.RESEARCH_UNIVERSE",["AAA"]), \
                 patch("candidate_feature_oos.bars",return_value=sample) as download, \
                 patch("candidate_feature_oos.compare",return_value={"status":"NO_SIGNALS"}), \
                 patch("candidate_feature_oos.evaluate_filtered",
                       return_value={"status":"NO_FILTERED_SIGNALS"}), \
                 patch("candidate_feature_oos.portfolio_oos_pair",
                       return_value={"comparison_status":"NO_BASELINE_OUT_OF_SAMPLE_SIGNALS"}) as paired, \
                 patch("candidate_feature_oos.Path",
                       side_effect=lambda p: Path(folder)/p):
                main()
            report=json.loads((Path(folder)/"reports/candidate_feature_oos.json").read_text())
        self.assertEqual(len(report["portfolio_oos"]),2)
        self.assertEqual(report["input_data_provenance"]["benchmark"]["rows"],800)
        self.assertEqual(report["input_data_provenance"]["stocks"]["AAA"]["rows"],800)
        self.assertEqual(len(report["input_data_provenance"]["stocks"]["AAA"]["sha256"]),64)
        self.assertEqual(report["input_data_provenance"]["benchmark"]["sha256"],report["input_data_provenance"]["stocks"]["AAA"]["sha256"])
        self.assertFalse(report["input_data_provenance"]["data_frozen"])
        self.assertEqual(paired.call_count,2)
        self.assertEqual(download.call_count,2)  # SPY and AAA, not twice per pattern
        self.assertEqual(report["portfolio_oos_provenance"]["loaded_symbols"],["AAA"])
        self.assertFalse(report["portfolio_oos_provenance"]["trade_ready"])


if __name__=="__main__":
    unittest.main()
