"""Offline demonstration of immutable EU prospective candidate receipts.

Synthetic data only. The real EU index identity gate remains blocked.
"""
import json
from research_europe_candidate_registry_bridge import register_snapshot
from research_europe_prospective_protocol import evaluate_readiness

def demonstrate():
    snapshot={"symbol":"SYNTHETIC.EU","decision_day":"2026-11-09",
              "as_of_complete_day":"2026-11-09","pattern":"eu-recovery",
              "selected":False,"features":{"relative_strength_20d_pp":-7.25},
              "source_sha256":"a"*64,"research_only":True,"trade_ready":False}
    # True is *only* a synthetic fixture to exercise the positive path.
    entry=register_snapshot(snapshot,decision_cutoff="2026-11-09",
                            benchmark_identity_verified=True)
    readiness=evaluate_readiness([entry],start_day="2026-11-09",end_day="2026-11-09")
    tampered=dict(entry,selected=True)
    detected=False
    try:
        evaluate_readiness([tampered],start_day="2026-11-09",end_day="2026-11-09")
    except ValueError as exc:
        detected=str(exc)=="DECISION_TAMPERED"
    if not detected:raise AssertionError("TAMPER_GATE_FAILED")
    return {"synthetic_fixture":True,"live_benchmark_identity_verified":False,
            "decision_sha256":entry["decision_sha256"],"tamper_detected":detected,
            "minimum_observation_met":readiness["minimum_observation_met"],
            "trade_ready":False,"orders_placed":False}

if __name__=="__main__":
    print(json.dumps(demonstrate(),sort_keys=True,indent=2))
