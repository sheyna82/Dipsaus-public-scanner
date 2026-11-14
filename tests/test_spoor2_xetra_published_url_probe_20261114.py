import unittest
import urllib.error
from research.spoor2_xetra_published_url_probe_20261114 import probe_published_url, PUBLISHED


class FakeResponse:
    status = 200
    def __init__(self, url):
        self.url = url
    def geturl(self):
        return self.url
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []
    def open(self, request, timeout=None):
        self.calls.append((request.full_url, request.get_method(), timeout))
        if isinstance(self.outcome, Exception):
            raise self.outcome
        return self.outcome


class PublishedUrlProbeTests(unittest.TestCase):
    def test_valid_response_still_unattested(self):
        op = FakeOpener(FakeResponse(PUBLISHED["csv"]))
        r = probe_published_url("csv", op)
        self.assertEqual(op.calls, [(PUBLISHED["csv"], "HEAD", 15)])
        self.assertEqual(r["http_status"], 200)
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["order_placement_enabled"])

    def test_redirect_not_followed_and_location_not_exposed(self):
        target = "https://www.cashmarket.deutsche-boerse.com/resource/blob/other?token=secret"
        err = urllib.error.HTTPError(PUBLISHED["zip"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("zip", FakeOpener(err))
        self.assertEqual(r["http_status"], 302)
        self.assertEqual(len(r["location_sha256"]), 64)
        self.assertNotIn("secret", str(r))
        self.assertTrue(r["redirect_not_followed"])
        self.assertEqual(r["redirect_target_class"], "OTHER_OR_UNSAFE")

    def test_same_host_blob_redirect_still_unattested(self):
        target = "https://www.cashmarket.deutsche-boerse.com/resource/blob/99/abc/data/file.csv"
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertEqual(r["redirect_target_class"], "SAME_HOST_BLOB_PATH_UNATTESTED")
        self.assertFalse(r["expected_filename_matches"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])

    def test_matching_filename_still_unattested(self):
        target = PUBLISHED["csv"].replace("/1528/", "/9999/")
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertTrue(r["expected_filename_matches"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])

    def test_canonical_blob_shape_without_attestation(self):
        target = PUBLISHED["csv"].replace("/1528/", "/9999/")
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertTrue(r["canonical_blob_shape_matches"])
        self.assertFalse(r["blob_id_matches_published"])
        self.assertTrue(r["blob_token_matches_published"])
        self.assertFalse(r["redirect_equals_published_url"])
        self.assertFalse(r["source_attested"])

    def test_changed_blob_token_is_reported_without_disclosure(self):
        target = PUBLISHED["zip"].replace("6ddad5f38f99a491ee1ebe750759e833", "a" * 32)
        err = urllib.error.HTTPError(PUBLISHED["zip"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("zip", FakeOpener(err))
        self.assertTrue(r["blob_id_matches_published"])
        self.assertFalse(r["blob_token_matches_published"])
        self.assertNotIn("a" * 32, str(r))
        self.assertFalse(r["source_attested"])

    def test_redirect_equals_legacy_url_still_blocked(self):
        from research.spoor2_xetra_artifact_retrieval_20261113 import SOURCES
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found",
                                     {"Location": SOURCES["csv"]}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertTrue(r["redirect_equals_legacy_url"])
        self.assertFalse(r["redirect_equals_published_url"])
        self.assertFalse(r["source_attested"])
        self.assertFalse(r["trade_ready"])

    def test_noncanonical_blob_shape_remains_blocked(self):
        target = "https://www.cashmarket.deutsche-boerse.com/resource/blob/abc/data/t7-xetr-allTradableInstruments.csv"
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertFalse(r["canonical_blob_shape_matches"])
        self.assertFalse(r["trade_ready"])

    def test_backslash_redirect_classified_unsafe(self):
        target = PUBLISHED["csv"].replace("/data/", "/data/" + chr(92))
        err = urllib.error.HTTPError(PUBLISHED["csv"], 302, "Found", {"Location": target}, None)
        r = probe_published_url("csv", FakeOpener(err))
        self.assertEqual(r["redirect_target_class"], "OTHER_OR_UNSAFE")
        self.assertFalse(r["source_attested"])

    def test_unhashable_kind_fails_closed(self):
        r = probe_published_url(["csv"])
        self.assertIsNone(r["kind"])
        self.assertEqual(r["failure_category"], "INVALID_KIND")

    def test_unexpected_final_url_blocked(self):
        r = probe_published_url("csv", FakeOpener(FakeResponse("https://example.org")))
        self.assertEqual(r["failure_category"], "UNEXPECTED_REDIRECT")
        self.assertFalse(r["source_attested"])


if __name__ == "__main__":
    unittest.main()
