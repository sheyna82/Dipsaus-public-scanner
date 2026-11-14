"""Verify pinned snapshot source identifiers and separately computed SHA256."""
import json
import unittest
from pathlib import Path


class RuntimeManifestTests(unittest.TestCase):
    def test_manifest_tracks_immutable_blob_ids_not_sha256(self):
        path = Path("research/evidence/spoor2_runtime_snapshot_manifest_20261111.json")
        manifest = json.loads(path.read_text(encoding="utf-8"))
        self.assertFalse(manifest["trade_ready"])
        self.assertFalse(manifest["live_changes"])
        self.assertEqual(sum(x["candidate_count"] for x in manifest["sources"]), 477)
        self.assertEqual(sum(x["schema_blocked_count"] for x in manifest["sources"]), 0)
        self.assertEqual({x["market"] for x in manifest["sources"]}, {"US", "EU"})
        for source in manifest["sources"]:
            self.assertEqual(len(source["git_blob_sha"]), 40)
            self.assertGreater(source["size_bytes"], 0)
            self.assertEqual(len(source["sha256"]), 64)
            int(source["sha256"], 16)
        self.assertIn("remains unverified", manifest["verification_scope"])


if __name__ == "__main__":
    unittest.main()
