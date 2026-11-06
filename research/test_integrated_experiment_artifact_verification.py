"""Offline experiment artifact verification tests."""
import hashlib
import unittest
from integrated_experiment_registry import register_research_experiment
from integrated_experiment_artifact_verification import verify_experiment_artifacts

DATA = b"frozen historical dataset\n"
SOURCE = b"official source fixture\n"
OUTCOME = b"oos outcome fixture\n"


def h(data):
    return hashlib.sha256(data).hexdigest()


def manifest():
    return register_research_experiment(
        experiment_id="artifact-check-001",
        commit_sha="a" * 40,
        dataset_sha256=h(DATA),
        source_sha256=[h(SOURCE)],
        config={"entry": "next_open", "cost_pct": 0.5},
        split_definition={"oos_start": "2026-01-01"},
        benchmark_id="us21",
        outcome_sha256=h(OUTCOME),
    )


class ExperimentArtifactVerificationTests(unittest.TestCase):
    def test_exact_bytes_verified(self):
        result = verify_experiment_artifacts(
            manifest(), dataset_bytes=DATA, source_blobs=[SOURCE], outcome_bytes=OUTCOME)
        self.assertTrue(result["dataset_bytes_verified"])
        self.assertTrue(result["outcome_bytes_verified"])
        self.assertEqual(result["source_bytes_verified"], 1)
        self.assertFalse(result["out_of_sample_performance_independently_proven"])

    def test_dataset_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXPERIMENT_DATASET_HASH_MISMATCH"):
            verify_experiment_artifacts(
                manifest(), dataset_bytes=DATA + b"x",
                source_blobs=[SOURCE], outcome_bytes=OUTCOME)

    def test_source_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXPERIMENT_SOURCE_HASH_MISMATCH"):
            verify_experiment_artifacts(
                manifest(), dataset_bytes=DATA,
                source_blobs=[SOURCE + b"x"], outcome_bytes=OUTCOME)

    def test_outcome_tamper_rejected(self):
        with self.assertRaisesRegex(ValueError, "EXPERIMENT_OUTCOME_HASH_MISMATCH"):
            verify_experiment_artifacts(
                manifest(), dataset_bytes=DATA,
                source_blobs=[SOURCE], outcome_bytes=OUTCOME + b"x")


if __name__ == "__main__":
    unittest.main()
