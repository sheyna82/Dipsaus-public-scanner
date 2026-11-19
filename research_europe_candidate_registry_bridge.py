"""Isolated bridge from frozen candidate snapshots to forward-only registry.

No provider calls, orders, or changes to live selection. Fail closed.
"""
from research_europe_prospective_protocol import register_candidate

REQUIRED=("symbol","decision_day","pattern","selected","features","source_sha256")

def register_snapshot(snapshot, *,decision_cutoff,benchmark_identity_verified=False,synthetic_fixture=False):
    if not isinstance(snapshot,dict):raise ValueError("INVALID_SNAPSHOT")
    missing=[k for k in REQUIRED if k not in snapshot]
    if missing:raise ValueError("MISSING_SNAPSHOT_FIELDS:"+",".join(missing))
    if "outcome" in snapshot or "forward_return" in snapshot or "exit_price" in snapshot:
        raise ValueError("LOOKAHEAD_SNAPSHOT")
    if snapshot.get("research_only") is not True or snapshot.get("trade_ready") is not False:
        raise ValueError("NOT_ISOLATED_RESEARCH")
    if snapshot.get("as_of_complete_day")!=snapshot["decision_day"]:
        raise ValueError("SNAPSHOT_DAY_MISMATCH")
    if benchmark_identity_verified is True and synthetic_fixture is not True:
        raise ValueError("INDEPENDENT_BENCHMARK_RECEIPT_REQUIRED")
    if synthetic_fixture is True and snapshot["symbol"]!="SYNTHETIC.EU":
        raise ValueError("SYNTHETIC_FIXTURE_ONLY")
    return register_candidate(symbol=snapshot["symbol"],
        decision_day=snapshot["decision_day"],pattern=snapshot["pattern"],
        selected=snapshot["selected"],decision_cutoff=decision_cutoff,
        features=snapshot["features"],source_sha256=snapshot["source_sha256"],
        benchmark_identity_verified=benchmark_identity_verified)
