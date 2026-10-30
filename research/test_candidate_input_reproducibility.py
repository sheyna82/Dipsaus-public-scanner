import unittest
from candidate_input_reproducibility import compare_reports


def report(benchmark="a", stocks=None):
    return {"input_data_provenance":{
        "hash_algorithm":"sha256_canonical_json_sorted_keys",
        "benchmark":{"sha256":benchmark},
        "stocks":stocks if stocks is not None else {"AAA":{"sha256":"x"}}}}


class InputReproducibilityTests(unittest.TestCase):
    def test_identical(self):
        result=compare_reports(report(),report())
        self.assertEqual(result["status"],"IDENTICAL_INPUTS")
        self.assertTrue(result["identical_inputs"])

    def test_benchmark_and_universe_change(self):
        result=compare_reports(report(),report("b",{"BBB":{"sha256":"z"}}))
        self.assertTrue(result["benchmark_changed"])
        self.assertEqual(result["added_symbols"],["BBB"])
        self.assertEqual(result["removed_symbols"],["AAA"])
        self.assertFalse(result["identical_inputs"])

    def test_stock_revision(self):
        result=compare_reports(report(),report(stocks={"AAA":{"sha256":"y"}}))
        self.assertEqual(result["changed_symbols"],["AAA"])

    def test_missing_hashes_blocked(self):
        self.assertEqual(compare_reports({},report())["status"],
                         "BLOCKED_MISSING_INPUT_HASHES")


if __name__=="__main__":
    unittest.main()
