"""Offline aggregation of verified ZIP artifacts, with duplicate-window rejection."""
from research_finnhub_artifact_inventory_bridge import inventory_from_artifact

def build_artifact_collection(artifacts):
    if not isinstance(artifacts, (list, tuple)) or not artifacts:
        raise ValueError("artifact_inputs_required")
    entries = []
    receipts = []
    windows = set()
    digests = set()
    for archive, expected_digest in artifacts:
        result = inventory_from_artifact(archive, expected_zip_sha256=expected_digest)
        digest = result["zip_sha256"]
        if digest in digests:
            raise ValueError("duplicate_artifact")
        digests.add(digest)
        observations = result["inventory"]["observations"]
        for observation in observations:
            identity = (observation["symbol"], observation["request_started_utc"],
                        observation["response_finished_utc"])
            if identity in windows:
                raise ValueError("duplicate_observation_window")
            windows.add(identity)
            entries.append(observation)
        receipts.append({"zip_sha256": digest,
                         "observation_json_sha256": result["observation_json_sha256"]})
    entries.sort(key=lambda x: (x["request_started_utc"], x["symbol"], x["response_finished_utc"]))
    receipts.sort(key=lambda x: x["zip_sha256"])
    return {"schema": "dipsaus_research_artifact_collection_v1",
            "count": len(entries), "observations": entries, "artifact_receipts": receipts,
            "quote_accuracy_verified": False, "prospective_signal_proven": False,
            "research_only": True, "trade_ready": False}
