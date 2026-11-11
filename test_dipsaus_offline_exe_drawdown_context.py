import unittest
from dipsaus_offline_exe_drawdown_context import summarize_span_drawdown


class DrawdownContextTests(unittest.TestCase):
    def test_measures_observed_peak_to_close(self):
        bars = [{"open": 100., "high": 101., "low": 99., "close": 100.},
                {"open": 100., "high": 100., "low": 98., "close": 98.5}]
        result = summarize_span_drawdown(bars)
        self.assertEqual(result["status"], "DESCRIPTIVE_ONLY")
        self.assertEqual(result["worst_peak_to_close_pct"], round((98.5/101-1)*100, 4))
        self.assertEqual(result["worst_index"], 1)

    def test_invalid_bar_blocks(self):
        self.assertEqual(summarize_span_drawdown(
            [{"open": 100., "high": 99., "low": 98., "close": 100.}])["status"],
            "DATA_BLOCKED")


if __name__ == "__main__":
    unittest.main()
