"""Offline-only CSV parser tests; no external requests."""
import unittest
from research_event_stooq_acquisition import parse_stooq_csv, acquire_stooq_history

HEADER = b"Date,Open,High,Low,Close,Volume\n"


class HistoricalCsvTests(unittest.TestCase):
    def test_synthetic_csv_parsed_without_market_claims(self):
        rows = parse_stooq_csv(HEADER +
            b"2026-10-20,100,102,99,101,1000\n"
            b"2026-10-21,101,103,100,102,1500\n")
        self.assertEqual(rows[1]["close"], "102")
        self.assertEqual(rows[0]["date"], "2026-10-20")

    def test_malformed_and_unsorted_csv_rejected(self):
        for payload in (
            b"Error: data unavailable",
            HEADER,
            HEADER + b"2026-10-20,1,2,1,NaN,10\n",
            HEADER + b"2026-10-21,1,2,1,2,10\n"
                     b"2026-10-20,1,2,1,2,10\n",
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    parse_stooq_csv(payload)

    def test_impossible_ohlc_rows_rejected(self):
        for line in (
            b"2026-10-20,100,99,98,101,1000\\n",
            b"2026-10-20,100,102,101,101,1000\\n",
            b"2026-10-20,100,102,98,-1,1000\\n",
            b"2026-10-20,100,102,98,101,-1\\n",
        ):
            with self.subTest(line=line):
                with self.assertRaisesRegex(ValueError, "invalid_csv_observation"):
                    parse_stooq_csv(HEADER + line)

    def test_network_is_opt_in(self):
        with self.assertRaisesRegex(ValueError, "explicit_network_opt_in_required"):
            acquire_stooq_history("AMD", "2026-10-01", "2026-10-23", "/tmp/unused")


if __name__ == "__main__":
    unittest.main()
