"""Verify research branch is intentionally blocked until exact protocol is imported.

Run independently of other test modules. A false green activation is an error.
"""
import json
from integrated_evidence_readiness import readiness

def main():
    result = readiness()
    if result != {"status": "BLOCKED_PROTOCOL_NOT_IMPORTED", "trade_ready": False}:
        raise RuntimeError("UNEXPECTED_RESEARCH_READINESS: " + repr(result))
    print(json.dumps({"gate": "PASS_EXPECTED_BLOCK", "readiness": result,
                      "activation": False}, sort_keys=True))

if __name__ == "__main__":
    main()
