"""Fail-closed classification of static EU legacy calls; audit only.

Unknown call sites are reported and cause the CI gate to fail. This scanner
cannot prove the absence of reflection, dynamic imports or external consumers.
"""
from pathlib import Path
from research_audit_europe_legacy_calls import inventory, tracked_python_files

CONTROLLED = {
    ("research_europe_relative_strength_admitted.py", "research_europe_relative_strength.compare"),
    ("research_europe_recovery_confirmation_admitted.py", "research_europe_recovery_confirmation.evaluate"),
}
HISTORICAL_TESTS = {
    "test_research_europe_relative_strength.py",
    "test_research_europe_recovery_confirmation.py",
}

def classify(hits):
    classified = []
    for hit in hits:
        path = Path(hit["path"]).as_posix()
        name = Path(path).name
        key = (path, hit["target"])
        if hit.get("kind") == "dynamic_import":
            category = "unreviewed_direct_call"
        elif key in CONTROLLED:
            category = "controlled_delegation"
        elif path == name and name in HISTORICAL_TESTS:
            category = "historical_test"
        else:
            category = "unreviewed_direct_call"
        classified.append({**hit, "classification": category})
    return classified

def enforce_no_unreviewed(hits):
    unknown = [x for x in classify(hits) if x["classification"] == "unreviewed_direct_call"]
    if unknown:
        raise ValueError("UNREVIEWED_LEGACY_EU_CALLS:" + str(len(unknown)))
    return classify(hits)

if __name__ == "__main__":
    import json
    rows = classify(inventory(tracked_python_files()))
    print(json.dumps({"schema": "dipsaus_eu_legacy_call_review_v1",
                      "audit_only": True, "call_sites": rows}, sort_keys=True, indent=2))
    enforce_no_unreviewed(rows)
