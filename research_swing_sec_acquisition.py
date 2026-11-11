"""Opt-in SEC submissions acquisition for an offline historical pilot.

No implicit requests; caller must supply an honest SEC-compliant User-Agent.
The endpoint is public but access can be throttled or denied.
"""
import argparse
import json
import time
from pathlib import Path
from urllib.request import Request, urlopen
from research_swing_sec_submissions import sec_submissions_endpoint
from research_swing_sec_batch_import import import_sec_json_files

MAX_COMPANIES = 10


def download_sec_submissions(ciks, *, user_agent, output_dir, pause_seconds=1.0):
    if not isinstance(user_agent, str) or len(user_agent.strip()) < 12 or "@" not in user_agent:
        raise ValueError("sec_contact_user_agent_required")
    if not isinstance(ciks, (list, tuple)) or not 1 <= len(ciks) <= MAX_COMPANIES:
        raise ValueError("invalid_company_count")
    if len(set(ciks)) != len(ciks):
        raise ValueError("duplicate_cik")
    if type(pause_seconds) not in (int, float) or pause_seconds < 1:
        raise ValueError("insufficient_request_spacing")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    paths = []
    for index, cik in enumerate(ciks):
        endpoint = sec_submissions_endpoint(cik)
        if index:
            time.sleep(pause_seconds)
        request = Request(endpoint, headers={
            "User-Agent": user_agent, "Accept": "application/json"})
        with urlopen(request, timeout=20) as response:
            raw = response.read(15_000_001)
        if len(raw) > 15_000_000:
            raise ValueError("response_too_large")
        payload = json.loads(raw)
        if payload.get("cik") != cik:
            raise ValueError("cik_mismatch")
        path = directory / f"CIK{cik:010d}.json"
        path.write_bytes(raw)
        paths.append(path)
    return import_sec_json_files(paths)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cik", type=int, action="append", required=True)
    parser.add_argument("--user-agent", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    result = download_sec_submissions(
        args.cik, user_agent=args.user_agent, output_dir=args.out_dir)
    out = Path(args.out_dir) / "candidate_manifest.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"SEC filing candidates: {result['candidate_count']} (not trade eligible)")


if __name__ == "__main__":
    main()
