import unittest
from unittest.mock import patch
from research_reproduce_plotly_aapl import download_example_prices, run_example


class FakeResponse:
    def __init__(self, content):
        self.content = content
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.content[:n]


class RealDataPilotTests(unittest.TestCase):
    def test_rejects_unexpected_source_shape(self):
        with patch("research_reproduce_plotly_aapl.urlopen",
                   return_value=FakeResponse(b"Date,Close\n2020-01-01,100\n")):
            with self.assertRaisesRegex(ValueError, "unexpected_columns"):
                download_example_prices()

    def test_rejects_truncated_dataset(self):
        raw = b"Date,AAPL.Open,AAPL.High,AAPL.Low,AAPL.Close,AAPL.Volume\n2020-01-01,1,2,1,2,10\n"
        with patch("research_reproduce_plotly_aapl.urlopen",
                   return_value=FakeResponse(raw)):
            with self.assertRaisesRegex(ValueError, "unexpected_dataset_version"):
                download_example_prices()

    def test_rejects_oversized_dataset(self):
        with patch("research_reproduce_plotly_aapl.urlopen",
                   return_value=FakeResponse(b"x" * 250001)):
            with self.assertRaisesRegex(ValueError, "example_dataset_too_large"):
                download_example_prices()


if __name__ == "__main__":
    unittest.main()
