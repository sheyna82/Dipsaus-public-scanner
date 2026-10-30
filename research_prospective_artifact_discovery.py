"""Read-only research artifact discovery from GitHub's REST API.

No token is printed or persisted. This is a metadata-only lookup; it does not
download archives or claim that previous-run restoration is validated.
"""
import json
from urllib.parse import quote
from urllib.request import Request, urlopen

from research_prospective_previous_run_selection import select_previous_artifact


def discover_previous_archive(repo, token, current_run_id, artifact_name,
                              now_iso, *, opener=urlopen, max_pages=5):
    if not token:
        raise ValueError("github_token_required")
    if len(repo.split("/")) != 2 or any(
        not part.replace("-", "").replace("_", "").isalnum()
        for part in repo.split("/")
    ):
        raise ValueError("invalid_repository")
    if not 1 <= max_pages <= 10:
        raise ValueError("invalid_page_limit")
    found = []
    for page in range(1, max_pages + 1):
        url = ("https://api.github.com/repos/" + repo
               + "/actions/artifacts?per_page=100&page=" + str(page))
        req = Request(url, headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "DIPSAUS-research-read-only"})
        with opener(req, timeout=15) as response:
            payload = json.load(response)
        batch = payload.get("artifacts")
        if not isinstance(batch, list):
            raise ValueError("invalid_github_artifacts_response")
        found.extend(batch)
        if len(batch) < 100:
            break
    selection = select_previous_artifact(
        found, current_run_id=current_run_id,
        artifact_name=artifact_name, now_iso=now_iso)
    selection["metadata_pages_checked"] = page
    selection["metadata_only"] = True
    selection["cross_run_restoration_performed"] = False
    return selection
