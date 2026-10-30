"""Offline SEC filing batch ingestion from real, externally downloaded JSON.

Usage:
 python research_swing_sec_batch_import.py submissions1.json submissions2.json --out sec_candidates.json
No HTTP requests. No fabricated event release timestamps or trade signals.
"""
import argparse
import hashlib
import json
from pathlib import Path
from research_swing_sec_submissions import normalize_sec_recent_filings


def import_sec_json_files(paths):
    if not paths:
        raise ValueError("no_input_files")
    output = []
    seen = set()
    sources = []
    for item in paths:
        path = Path(item)
        raw = path.read_bytes()
        payload = json.loads(raw)
        filings = normalize_sec_recent_filings(payload)
        digest = hashlib.sha256(raw).hexdigest()
        sources.append({"file_name": path.name, "sha256": digest,
                        "filing_candidates": len(filings)})
        for filing in filings:
            identity = (filing["cik"], filing["accession"])
            if identity in seen:
                raise ValueError("duplicate_filing_across_files")
            seen.add(identity)
            output.append({**filing, "source_file_sha256": digest})
    output.sort(key=lambda item: (item["cik"], item["filing_date"], item["accession"]))
    return {"schema_version": 1, "sources": sources,
            "candidate_count": len(output), "candidates": output,
            "historical_release_times_verified": False, "trade_ready": False}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", help="SEC submissions JSON downloaded separately")
    parser.add_argument("--out", required=True, help="output JSON file")
    args = parser.parse_args(argv)
    result = import_sec_json_files(args.files)
    Path(args.out).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("SEC filing candidates:", result["candidate_count"],
          "from source files:", len(result["sources"]))


if __name__ == "__main__":
    main()
