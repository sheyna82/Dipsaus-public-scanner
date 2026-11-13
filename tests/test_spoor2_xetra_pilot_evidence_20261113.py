import csv
import io
import unittest
import zipfile
from research.spoor2_xetra_pilot_evidence_20261113 import build_pilot_evidence

HEADER = ["Instrument", "ISIN", "MIC Code", "Market Segment", "Product Status", "Product ID"]

def fixture_csv(rows):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerows([["Market:", "XETR"], ["Date Last Update:", "13.11.2026"], HEADER] + rows)
    return output.getvalue().encode()

def fixture_zip():
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("20261113_marketSegment.csv",
            "Content type;Identifier;Description\nMarket Segment;045;Regulierter Markt Prime Standard\n")
    return output.getvalue()

ROWS = [["Infineon", "DE0006231004", "XETR", "045", "Active", "52931"],
        ["Rheinmetall", "DE0007030009", "XETR", "045", "Active", "52978"]]

class TestPilotEvidence(unittest.TestCase):
    def test_both_join_but_no_attestation(self):
        result = build_pilot_evidence(fixture_csv(ROWS), fixture_zip())
        self.assertEqual(len(result["records"]), 2)
        self.assertEqual(result["records"][0]["market_segment_description"], "Regulierter Markt Prime Standard")
        for key in ("source_attested", "instrument_segment_verified", "segment_mic_verified",
                    "broker_route_verified", "degiro_fee_verified", "trade_ready", "order_placement_enabled"):
            self.assertFalse(result[key])

    def test_missing_isin_blocks(self):
        result = build_pilot_evidence(fixture_csv(ROWS[:1]), fixture_zip())
        self.assertIn("MISSING_OR_AMBIGUOUS_ISIN_DE0007030009", result["blocks"])

    def test_duplicate_isin_blocks(self):
        result = build_pilot_evidence(fixture_csv(ROWS + ROWS[:1]), fixture_zip())
        self.assertIn("MISSING_OR_AMBIGUOUS_ISIN_DE0006231004", result["blocks"])

    def test_wrong_market_blocks(self):
        rows = [list(row) for row in ROWS]
        rows[0][2] = "XAMS"
        result = build_pilot_evidence(fixture_csv(rows), fixture_zip())
        self.assertIn("UNMATCHED_MARKET_OR_SEGMENT_DE0006231004", result["blocks"])

    def test_invalid_zip_blocks(self):
        result = build_pilot_evidence(fixture_csv(ROWS), b"bad")
        self.assertIn("INVALID_REFERENCE_ZIP", result["blocks"])

if __name__ == "__main__":
    unittest.main()
