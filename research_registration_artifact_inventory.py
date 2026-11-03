"""Research-only GitHub artifact inventory with explicit pagination completeness.

Metadata is advisory; it never authenticates downloaded bytes or timestamps.
"""
import json
from urllib.request import Request, urlopen


def inventory_candidate_artifacts(repo, token, artifact_name, *,
                                  opener=urlopen, max_pages=5):
    if not token:
        raise ValueError("github_token_required")
    parts = repo.split("/")
    if len(parts) != 2 or any(not p or not p.replace("-", "").replace("_", "").isalnum()
                              for p in parts):
        raise ValueError("invalid_repository")
    if not isinstance(max_pages, int) or not 1 <= max_pages <= 10:
        raise ValueError("invalid_page_limit")
    found = []
    pages = 0
    exhausted = False
    for page in range(1, max_pages + 1):
        url = f"https://api.github.com/repos/{repo}/actions/artifacts?per_page=100&page={page}"
        req = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DIPSAUS-research-read-only"})
        with opener(req, timeout=15) as response:
            data = json.load(response)
        batch = data.get("artifacts")
        if not isinstance(batch, list) or len(batch) > 100:
            raise ValueError("invalid_github_artifacts_response")
        pages += 1
        found.extend(batch)
        if len(batch) < 100:
            exhausted = True
            break
    matching = [a for a in found if a.get("name") == artifact_name]
    ids = [a.get("id") for a in matching]
    if any(not isinstance(i, int) or i <= 0 for i in ids) or len(ids) != len(set(ids)):
        raise ValueError("invalid_or_duplicate_artifact_ids")
    return {"status": "metadata_pages_exhausted" if exhausted else "pagination_limit_reached",
            "metadata_pages_checked": pages,
            "artifact_ids": sorted(ids),
            "metadata_inventory_exhausted": exhausted,
            "historical_run_coverage_proven": False,
            "artifact_bytes_authenticated": False,
            "research_only": True, "trade_ready": False}
