"""Compare immutable input digests between two research report artifacts.

Run: python research/candidate_input_reproducibility.py old.json new.json
Research only; no broker access or order placement.
"""
import json
import sys


def compare_reports(old, new):
    a = old.get("input_data_provenance")
    b = new.get("input_data_provenance")
    if not isinstance(a, dict) or not isinstance(b, dict):
        return {"status": "BLOCKED_MISSING_INPUT_HASHES", "comparable": False}
    if a.get("hash_algorithm") != b.get("hash_algorithm"):
        return {"status": "BLOCKED_HASH_ALGORITHM_MISMATCH", "comparable": False}
    old_stocks, new_stocks = a.get("stocks", {}), b.get("stocks", {})
    if not isinstance(old_stocks, dict) or not isinstance(new_stocks, dict):
        return {"status": "BLOCKED_INVALID_STOCK_PROVENANCE", "comparable": False}
    changed = sorted(s for s in old_stocks.keys() & new_stocks.keys()
                     if old_stocks[s].get("sha256") != new_stocks[s].get("sha256"))
    old_benchmark, new_benchmark = a.get("benchmark", {}), b.get("benchmark", {})
    benchmark_changed = old_benchmark.get("sha256") != new_benchmark.get("sha256")
    added = sorted(new_stocks.keys() - old_stocks.keys())
    removed = sorted(old_stocks.keys() - new_stocks.keys())
    identical = not (changed or benchmark_changed or added or removed)
    return {
        "status": "IDENTICAL_INPUTS" if identical else "INPUTS_DIFFER",
        "comparable": True,
        "benchmark_changed": benchmark_changed,
        "changed_symbols": changed,
        "added_symbols": added,
        "removed_symbols": removed,
        "identical_inputs": identical,
        "trade_ready": False,
        "limitations": ["Hash comparison cannot identify which bars changed",
                        "Identical inputs alone do not prove identical code or execution"],
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: candidate_input_reproducibility.py old.json new.json")
    with open(sys.argv[1], encoding="utf-8") as f:
        old = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        new = json.load(f)
    print(json.dumps(compare_reports(old, new), indent=2))


if __name__ == "__main__":
    main()
