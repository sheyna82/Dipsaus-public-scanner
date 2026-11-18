import csv
import hashlib
import io
import unittest
import zipfile
from unittest.mock import patch
from research.spoor2_xetra_uploaded_artifact_parser_20261118 import inspect_supplied_xetra_artifacts


def fixtures():
    header = ["ISIN", "Mnemonic", "Product Status", "Instrument Status",
              "MIC Code", "Trading Model Type", "Market Segment", "Reporting Market"]
    out = io.StringIO()
    out.write("Market:;XETR\nDate Last Update:;18.11.2026\n")
    writer = csv.DictWriter(out, fieldnames=header, delimiter=";")
    writer.writeheader()
    for isin, symbol in [("DE0006231004", "IFX"), ("DE0007030009", "RHM")]:
        writer.writerow(dict(zip(header, [isin, symbol, "Active", "Active",
                                          "XETR", "Continuous", "045", "XETA"])))
    csv_bytes = out.getvalue().encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("20261118_marketSegment.csv",
                   "Content type;Identifier;Description\n"
                   "Market Segment;045;Regulierter Markt Prime Standard\n")
    return csv_bytes, buf.getvalue()


class XetraArtifactParserTests(unittest.TestCase):
    def test_matching_offline_fixture_is_never_attested(self):
        csv_bytes, zip_bytes = fixtures()
        hashes = {"csv": hashlib.sha256(csv_bytes).hexdigest(),
                  "zip": hashlib.sha256(zip_bytes).hexdigest()}
        with patch("research.spoor2_xetra_uploaded_artifact_parser_20261118.EXPECTED_HASHES", hashes):
            r = inspect_supplied_xetra_artifacts(csv_bytes, zip_bytes)
        self.assertEqual(len(r["instruments"]), 2)
        self.assertEqual(r["instruments"]["DE0006231004"]["Reporting Market"], "XETA")
        for key in ("source_attested", "segment_mic_verified", "trade_ready",
                    "order_placement_enabled", "notify", "automatic_orders"):
            self.assertFalse(r[key])

    def test_unrecognized_artifacts_rejected_before_parsing(self):
        csv_bytes, zip_bytes = fixtures()
        with self.assertRaisesRegex(ValueError, "HASH_MISMATCH"):
            inspect_supplied_xetra_artifacts(csv_bytes, zip_bytes)

    def test_missing_target_isin_rejected(self):
        csv_bytes, zip_bytes = fixtures()
        csv_bytes = csv_bytes.replace(b"DE0007030009", b"DE0007030008")
        hashes = {"csv": hashlib.sha256(csv_bytes).hexdigest(),
                  "zip": hashlib.sha256(zip_bytes).hexdigest()}
        with patch("research.spoor2_xetra_uploaded_artifact_parser_20261118.EXPECTED_HASHES", hashes):
            with self.assertRaisesRegex(ValueError, "TARGET_INSTRUMENT_MISSING"):
                inspect_supplied_xetra_artifacts(csv_bytes, zip_bytes)


if __name__ == "__main__":
    unittest.main()
