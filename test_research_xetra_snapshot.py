"""Synthetic Xetra instrument and ZIP segment crosswalk tests."""
import hashlib
import io
import unittest
import zipfile
from research_xetra_snapshot import inspect_xetra_snapshot

CSV = (b"Market:;XETR\nDate Last Update:;18.11.2026\n"
       b"Product Status;Instrument Status;Instrument;ISIN;Mnemonic;MIC Code;Market Segment;Currency\n"
       b"Active;Active;INFINEON;DE0006231004;IFX;XETR;045;EUR\n"
       b"Active;Active;ASML;NL0010273215;ASME;XETR;003;EUR\n")
SEG = b"Content type;Identifier;Description\nMarket Segment;045;Regulierter Markt Prime Standard\nMarket Segment;003;Freiverkehr\n"


def zipped(content=SEG, name="20261118_marketSegment.csv"):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr(name, content)
    return buf.getvalue()


class XetraTests(unittest.TestCase):
    def check(self, raw=CSV, archive=None, **updates):
        archive = zipped() if archive is None else archive
        args = dict(instrument_sha256=hashlib.sha256(raw).hexdigest(),
                    zip_sha256=hashlib.sha256(archive).hexdigest(),
                    requested_isins=("DE0006231004", "NL0010273215"))
        args.update(updates)
        return inspect_xetra_snapshot(raw, archive, **args)

    def test_valid_but_non_executable(self):
        r = self.check()
        self.assertEqual(r["status"], "OFFLINE_XETRA_SNAPSHOT_CONSISTENT")
        self.assertEqual(r["instrument_count"], 2)
        self.assertEqual(r["instruments"]["DE0006231004"]["segment_description"], "Regulierter Markt Prime Standard")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["broker_route_verified"])

    def test_wrong_csv_digest(self):
        self.assertEqual(self.check(instrument_sha256="0"*64)["reason"], "DIGEST_MISMATCH")

    def test_wrong_zip_digest(self):
        self.assertEqual(self.check(zip_sha256="0"*64)["reason"], "DIGEST_MISMATCH")

    def test_wrong_market(self):
        self.assertEqual(self.check(raw=CSV.replace(b"Market:;XETR", b"Market:;XAMS"))["reason"], "UNEXPECTED_MARKET_OR_DATE")

    def test_wrong_date(self):
        self.assertEqual(self.check(expected_update="19.11.2026")["reason"], "UNEXPECTED_MARKET_OR_DATE")

    def test_missing_segment(self):
        self.assertEqual(self.check(archive=zipped(SEG.replace(b"045;", b"046;")))["reason"], "UNMAPPED_SEGMENT")

    def test_missing_requested_isin(self):
        self.assertEqual(self.check(requested_isins=("XX0000000000",))["reason"], "MISSING_OR_DUPLICATE_INSTRUMENT")

    def test_missing_zip_member(self):
        self.assertEqual(self.check(archive=zipped(name="other.csv"))["reason"], "MISSING_SEGMENT_TABLE")

    def test_corrupt_zip(self):
        self.assertEqual(self.check(archive=b"badzip")["reason"], "INVALID_SOURCE_FORMAT")

    def test_duplicate_instrument(self):
        line = b"Active;Active;INFINEON;DE0006231004;IFX;XETR;045;EUR\n"
        self.assertEqual(self.check(raw=CSV+line)["reason"], "MISSING_OR_DUPLICATE_INSTRUMENT")

    def test_inactive_not_research_active(self):
        raw = CSV.replace(b"Active;Active;INFINEON", b"Active;Inactive;INFINEON")
        self.assertFalse(self.check(raw=raw)["instruments"]["DE0006231004"]["research_active"])

    def test_missing_columns(self):
        self.assertEqual(self.check(raw=CSV.replace(b";Currency\n", b";Wrong\n"))["reason"], "MISSING_INSTRUMENT_COLUMNS")


if __name__ == "__main__":
    unittest.main()
