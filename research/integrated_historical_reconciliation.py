"""Fail-closed reconciliation of frozen research artifacts (offline only)."""
import hashlib
import json
from pathlib import Path

def canonical_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()

def reconcile(directory):
    root = Path(directory)
    protocol = json.loads((root / "prospective_filter_protocol_v1_1.json").read_text(encoding="utf-8"))
    expected = (root / "prospective_filter_protocol_v1_1.sha256").read_text(encoding="utf-8").strip()
    if canonical_digest(protocol) != expected:
        raise ValueError("PROTOCOL_DIGEST_MISMATCH")
    source = protocol["historical_source"]
    for name, digest in source["artifact_file_sha256"].items():
        if Path(name).name != name:
            raise ValueError("UNSAFE_ARTIFACT_FILENAME")
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError("SOURCE_ARTIFACT_MISMATCH:" + name)
    data = json.loads((root / "candidate_feature_oos.json").read_text(encoding="utf-8"))
    if data.get("research_only") is not True or data.get("trade_ready") is not False:
        raise ValueError("UNSAFE_HISTORICAL_STATUS")
    if data.get("horizon_sessions") != 10 or data.get("cost_bps") != 50:
        raise ValueError("HISTORICAL_ASSUMPTIONS_MISMATCH")
    observed = {
        pattern: {"candidate_n": len(item["candidate_audit"]),
                  "selected_n": sum(row["filter_selected"] is True for row in item["candidate_audit"])}
        for pattern, item in data["portfolio_oos"].items()
    }
    if observed != source["historical_candidate_counts"]:
        raise ValueError("HISTORICAL_CANDIDATE_COUNTS_MISMATCH")
    return {"status": "RESEARCH_ONLY_LOCAL_EVIDENCE_RECONCILED",
            "verified_artifacts": len(source["artifact_file_sha256"]),
            "candidate_counts": observed,
            "trade_ready": False, "prospective_validated": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        raise SystemExit("usage: integrated_historical_reconciliation.py ARTIFACT_DIRECTORY")
    print(json.dumps(reconcile(sys.argv[1]), sort_keys=True))
