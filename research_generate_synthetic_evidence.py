"""Generate an explicitly synthetic, non-tradable GitHub Actions research artifact."""
import hashlib
import json
import os
from pathlib import Path
from zipfile import ZipFile

from research_prospective_archive import archive_ledger


def generate_synthetic_evidence(output_dir, *, run_id, head_sha):
    if not str(run_id).isdigit() or len(head_sha) != 40 or any(c not in "0123456789abcdef" for c in head_sha):
        raise ValueError("invalid_run_provenance")
    root = Path(output_dir)
    if root.exists():
        raise FileExistsError("evidence_directory_exists")
    (root / "candidates").mkdir(parents=True)
    (root / "outcomes").mkdir()
    record = {"synthetic_data_only": True, "research_only": True,
              "trade_ready": False, "future_outcome": None,
              "github_run_id_claimed": str(run_id), "workflow_checkout_sha_claimed": head_sha,
              "workflow_checkout_sha_may_be_pr_merge": True}
    (root / "candidates" / "synthetic.json").write_text(
        json.dumps(record, sort_keys=True) + "\n")
    archive_path = root / "prospective-ledger-synthetic.zip"
    archive_ledger(root / "candidates", root / "outcomes", archive_path)
    digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    (root / "sha256.txt").write_text(digest + "  prospective-ledger-synthetic.zip\n")
    return {"sha256": digest, "synthetic_data_only": True, "trade_ready": False}


if __name__ == "__main__":
    generate_synthetic_evidence("synthetic-evidence",
        run_id=os.environ["GITHUB_RUN_ID"], head_sha=os.environ["GITHUB_SHA"])
