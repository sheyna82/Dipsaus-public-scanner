"""Offline tests for research experiment registry."""
import copy
import unittest
from integrated_experiment_registry import register_research_experiment, verify_research_experiment


def fixture():
    return register_research_experiment(
        experiment_id="recovery-oos-001",
        commit_sha="a" * 40,
        dataset_sha256="b" * 64,
        source_sha256=["c" * 64, "d" * 64],
        config={"entry": "next_open", "holding_days": [5, 10, 15], "cost_pct": 0.5},
        split_definition={"train_end": "2025-12-31", "oos_start": "2026-01-01"},
        benchmark_id="us21-buyhold",
        outcome_sha256="e" * 64,
    )


class ExperimentRegistryTests(unittest.TestCase):
    def test_deterministic_manifest(self):
        first = fixture()
        second = fixture()
        self.assertEqual(first, second)
        self.assertTrue(verify_research_experiment(first))
        self.assertFalse(first["manifest"]["out_of_sample_performance_independently_proven"])

    def test_mutated_config_fails(self):
        bundle = fixture()
        bundle["manifest"]["config"]["cost_pct"] = 0
        with self.assertRaisesRegex(ValueError, "EXPERIMENT_MANIFEST_MISMATCH"):
            verify_research_experiment(bundle)

    def test_forged_proof_flag_fails_even_if_rehashed(self):
        bundle = fixture()
        bundle["manifest"]["trade_ready"] = True
        with self.assertRaisesRegex(ValueError, "EXPERIMENT_MANIFEST_MISMATCH"):
            verify_research_experiment(bundle)

    def test_duplicate_sources_rejected(self):
        with self.assertRaisesRegex(ValueError, "DUPLICATE_EXPERIMENT_SOURCE_HASH"):
            register_research_experiment(
                experiment_id="x", commit_sha="a" * 40, dataset_sha256="b" * 64,
                source_sha256=["c" * 64, "c" * 64], config={"cost": 1},
                split_definition={"oos": "2026"}, benchmark_id="baseline")


if __name__ == "__main__":
    unittest.main()
