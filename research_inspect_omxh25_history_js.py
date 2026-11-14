"""Research-only immutable Nasdaq History.js capture and endpoint discovery.

This downloads the exact script referenced by a captured Nasdaq history HTML
page, records SHA256 and a conservative list of possible history-related URL
literals. It does NOT execute JavaScript, infer undocumented API parameters,
or approve official index EOD values.
"""
import json
import re
from pathlib import Path
from research_capture_omxh25_issuer_raw import capture

HISTORY_JS_URL = "https://beta.indexes.nasdaqomx.com/Scripts/History.js?v=2.0.0.0"

def inspect_script_receipt(receipt_path):
    receipt = json.loads(Path(receipt_path).read_text(encoding="utf-8"))
    import base64
    import hashlib
    raw = base64.b64decode(receipt["source_raw_base64"], validate=True)
    if (receipt["source_url"] != HISTORY_JS_URL
            or hashlib.sha256(raw).hexdigest() != receipt["source_sha256"]):
        raise ValueError("HISTORY_JS_RECEIPT_INVALID")
    script = raw.decode("utf-8")
    # Candidate references are inspection hints, never verified endpoints.
    literals = sorted(set(re.findall(r"""['"]([^'"]{1,220})['"]""", script)))
    candidates = [s for s in literals if ("histor" in s.lower() or
                  "index" in s.lower() or "api/" in s.lower())][:80]
    return {"status": "script_source_captured_candidate_paths_unverified",
            "source_sha256": receipt["source_sha256"],
            "script_bytes": len(raw), "candidate_literals": candidates,
            "historical_eod_endpoint_verified": False,
            "benchmark_identity_verified": False, "research_only": True,
            "trade_ready": False}

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        raise SystemExit("usage: python research_inspect_omxh25_history_js.py RAW_RECEIPT OUTPUT_INSPECTION")
    result = inspect_script_receipt(sys.argv[1])
    Path(sys.argv[2]).write_text(json.dumps(result, sort_keys=True, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="candidate_literals"}, sort_keys=True))
