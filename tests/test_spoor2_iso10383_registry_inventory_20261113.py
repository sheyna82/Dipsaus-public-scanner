import unittest
from research.spoor2_iso10383_registry_inventory_20261113 import inspect_iso_mic_csv

class Iso10383InventoryTests(unittest.TestCase):
    def test_csv_matches_are_not_attestation(self):
        data = b"MIC,OPERATING MIC,STATUS\nXETR,XETR,ACTIVE\nXETA,XETR,ACTIVE\n"
        result = inspect_iso_mic_csv(data)
        self.assertEqual(len(result["target_rows"]), 2)
        self.assertFalse(result["mic_registered"])
        self.assertFalse(result["trade_ready"])

    def test_malformed_csv_blocks(self):
        result = inspect_iso_mic_csv(b"MIC,OPERATING MIC,STATUS\nXETR,XETR\n")
        self.assertIn("INCONSISTENT_ISO_CSV_COLUMNS", result["blocks"])

    def test_empty_blocks(self):
        self.assertIn("INVALID_ISO_CSV_BYTES", inspect_iso_mic_csv(b"")["blocks"])

if __name__ == "__main__":
    unittest.main()
