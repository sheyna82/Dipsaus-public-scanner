"""Generate an offline coverage report from explicitly pinned, preserved JSON files.

This report never claims source authentication or trading validity.
"""
import argparse
import json
from research_finnhub_observation_inventory import build_inventory
from research_finnhub_observation_coverage import assess_observation_coverage

def assess_preserved_files(paths):
    inventory = build_inventory(paths)
    collection = {"schema":"dipsaus_research_artifact_collection_v1",
                  "count":inventory["count"],"observations":inventory["observations"],
                  "quote_accuracy_verified":False,"prospective_signal_proven":False,
                  "trade_ready":False}
    coverage = assess_observation_coverage(collection)
    return {"schema":"dipsaus_research_preserved_coverage_report_v1",
            "inventory":inventory,"coverage":coverage,
            "provider_authenticated":False,"trade_ready":False}

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("observation",nargs="+")
    args=parser.parse_args()
    print(json.dumps(assess_preserved_files(args.observation),sort_keys=True,indent=2))
