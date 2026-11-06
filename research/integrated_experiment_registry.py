"""Immutable-style research experiment manifest, inspired by Qlib tracking.

Only externally supplied hashes and identifiers are recorded. A manifest does
not verify those sources or establish any trading edge.
"""
import hashlib
import json
import re

_SHA = re.compile(r"^[a-f0-9]{64}$")
_COMMIT = re.compile(r"^[a-f0-9]{40}$")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def register_research_experiment(*, experiment_id, commit_sha, dataset_sha256,
                                 config, source_sha256, split_definition,
                                 benchmark_id, outcome_sha256=None):
    if not isinstance(experiment_id, str) or not 1 <= len(experiment_id) <= 128 or experiment_id.strip() != experiment_id:
        raise ValueError("INVALID_EXPERIMENT_ID")
    if not isinstance(commit_sha, str) or not _COMMIT.fullmatch(commit_sha):
        raise ValueError("INVALID_EXPERIMENT_COMMIT")
    if not isinstance(dataset_sha256, str) or not _SHA.fullmatch(dataset_sha256):
        raise ValueError("INVALID_EXPERIMENT_DATASET_HASH")
    if not isinstance(source_sha256, list) or not source_sha256 or any(
            not isinstance(x, str) or not _SHA.fullmatch(x) for x in source_sha256):
        raise ValueError("INVALID_EXPERIMENT_SOURCE_HASHES")
    if len(source_sha256) != len(set(source_sha256)):
        raise ValueError("DUPLICATE_EXPERIMENT_SOURCE_HASH")
    if not isinstance(config, dict) or not config or not isinstance(split_definition, dict) or not split_definition:
        raise ValueError("INVALID_EXPERIMENT_CONFIGURATION")
    if not isinstance(benchmark_id, str) or not benchmark_id.strip():
        raise ValueError("INVALID_EXPERIMENT_BENCHMARK")
    if outcome_sha256 is not None and (not isinstance(outcome_sha256, str) or not _SHA.fullmatch(outcome_sha256)):
        raise ValueError("INVALID_EXPERIMENT_OUTCOME_HASH")
    manifest = {
        "schema": "dipsaus_research_experiment_v1",
        "experiment_id": experiment_id,
        "commit_sha": commit_sha,
        "dataset_sha256": dataset_sha256,
        "source_sha256": sorted(source_sha256),
        "config": config,
        "split_definition": split_definition,
        "benchmark_id": benchmark_id,
        "outcome_sha256": outcome_sha256,
        "source_authenticity_independently_proven": False,
        "out_of_sample_performance_independently_proven": False,
        "trade_ready": False,
    }
    # Round-trip eliminates mutable aliases, unsupported objects and NaN/Inf.
    manifest = json.loads(_canonical(manifest))
    return {"manifest": manifest, "manifest_sha256": hashlib.sha256(_canonical(manifest)).hexdigest()}


def verify_research_experiment(bundle):
    if not isinstance(bundle, dict) or set(bundle) != {"manifest", "manifest_sha256"}:
        raise ValueError("INVALID_EXPERIMENT_BUNDLE")
    manifest = bundle["manifest"]
    if not isinstance(manifest, dict) or manifest.get("schema") != "dipsaus_research_experiment_v1":
        raise ValueError("INVALID_EXPERIMENT_SCHEMA")
    expected = register_research_experiment(
        experiment_id=manifest.get("experiment_id"),
        commit_sha=manifest.get("commit_sha"),
        dataset_sha256=manifest.get("dataset_sha256"),
        config=manifest.get("config"),
        source_sha256=manifest.get("source_sha256"),
        split_definition=manifest.get("split_definition"),
        benchmark_id=manifest.get("benchmark_id"),
        outcome_sha256=manifest.get("outcome_sha256"),
    )
    if manifest != expected["manifest"] or bundle.get("manifest_sha256") != expected["manifest_sha256"]:
        raise ValueError("EXPERIMENT_MANIFEST_MISMATCH")
    return True
