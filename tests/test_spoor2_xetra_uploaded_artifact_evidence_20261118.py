import unittest
from research.spoor2_xetra_uploaded_artifact_evidence_20261118 import (
    build_uploaded_xetra_evidence_report,
)


class UploadedXetraArtifactEvidenceTests(unittest.TestCase):
    def test_artifact_fingerprints_and_exact_isins(self):
        r = build_uploaded_xetra_evidence_report()
        self.assertEqual(r["csv_sha256"], "c3f9f7e63dd9b551338c29bda00aaade3e48ec71e035d0ce19348423402dc1ee")
        self.assertEqual(r["zip_sha256"], "1f740e68d775bb3ebc3f79f776860b29034d8a1e47443e56a9730679e0545a24")
        self.assertEqual([x["isin"] for x in r["rows"]],
                         ["DE0006231004", "DE0007030009"])

    def test_reporting_market_not_segment_mic(self):
        for x in build_uploaded_xetra_evidence_report()["rows"]:
            self.assertEqual(x["mic_code"], "XETR")
            self.assertEqual(x["reporting_market"], "XETA")
            self.assertIsNone(x["segment_mic"])
            self.assertFalse(x["reporting_market_is_segment_mic_attested"])
            self.assertEqual(x["market_segment"], "045")
            self.assertEqual(x["market_segment_description"], "Regulierter Markt Prime Standard")

    def test_user_upload_cannot_unlock_trading(self):
        r = build_uploaded_xetra_evidence_report()
        self.assertEqual(r["artifact_origin"], "USER_UPLOADED")
        for key in ("source_attested", "instrument_segment_verified",
                    "segment_mic_verified", "broker_route_verified",
                    "degiro_fee_verified", "trade_ready", "order_placement_enabled",
                    "notify", "automatic_orders"):
            self.assertFalse(r[key])


if __name__ == "__main__":
    unittest.main()
