import unittest
from research.spoor2_eu_fetch_preflight_20261111 import review_eu_fetch_request
HOSTS=("data.example.org",)
def check(url,hosts=HOSTS):
    return review_eu_fetch_request(url,allowed_hosts=hosts)
class FetchPreflightTests(unittest.TestCase):
    def test_allowlisted_https_is_not_fetch_permission(self):
        r=check("https://data.example.org/quote")
        self.assertEqual(r["status"],"OFFLINE_PREFLIGHT_ONLY")
        self.assertFalse(r["fetch_allowed"])
        self.assertFalse(r["trade_ready"])
    def test_http_blocked(self):
        self.assertIn("UNSAFE_URL",check("http://data.example.org/quote")["blocks"])
    def test_subdomain_spoof_blocked(self):
        self.assertIn("HOST_NOT_ALLOWLISTED",check("https://data.example.org.evil.test/")["blocks"])
    def test_credentials_blocked(self):
        self.assertIn("UNSAFE_URL",check("https://user:pass@data.example.org/")["blocks"])
    def test_private_ip_blocked(self):
        self.assertIn("IP_LITERAL_NOT_ALLOWED",check("https://127.0.0.1/",("127.0.0.1",))["blocks"])
    def test_redirect_fragment_blocked(self):
        self.assertIn("UNSAFE_URL",check("https://data.example.org/#secret")["blocks"])
    def test_port_blocked(self):
        self.assertIn("UNSAFE_URL",check("https://data.example.org:8443/")["blocks"])
    def test_whitespace_blocked(self):
        self.assertIn("URL_CONTROL_OR_WHITESPACE",check("https://data.example.org/\n")["blocks"])
    def test_encoded_authority_blocked_before_host_matching(self):
        result=check("https://data.example.org%2f.evil.test/quote")
        self.assertIn("UNSAFE_URL",result["blocks"])
        self.assertFalse(result["fetch_allowed"])
    def test_repeated_dot_allowlist_blocked(self):
        result=check("https://data.example.org/quote",("data..example.org",))
        self.assertIn("INVALID_ALLOWLIST",result["blocks"])
        self.assertFalse(result["trade_ready"])
    def test_malformed_dns_labels_in_allowlist_fail_closed(self):
        hosts=("-data.example.org", "data-.example.org",
               "a"*64+".example.org", "a"*254)
        for host in hosts:
            with self.subTest(host=host):
                result=check("https://data.example.org/quote",(host,))
                self.assertEqual(result["status"],"BLOCKED")
                self.assertIn("INVALID_ALLOWLIST",result["blocks"])
                self.assertFalse(result["fetch_allowed"])
    def test_valid_hyphenated_host_stays_offline_only(self):
        result=check("https://market-data.example.org/quote",
                     ("market-data.example.org",))
        self.assertEqual(result["status"],"OFFLINE_PREFLIGHT_ONLY")
        self.assertFalse(result["fetch_allowed"])
    def test_url_host_must_match_validated_allowlist_host(self):
        # A URL hostname is admitted only through an already validated allowlist.
        for url in ("https://data.example.org/quote",
                    "https://DATA.EXAMPLE.ORG:443/quote"):
            with self.subTest(url=url):
                result=check(url)
                self.assertEqual(result["status"],"OFFLINE_PREFLIGHT_ONLY")
                self.assertFalse(result["fetch_allowed"])
                self.assertFalse(result["trade_ready"])
        for host in ("data..example.org", "-data.example.org",
                     "data-.example.org", "data_example.org",
                     "a"*64+".example.org"):
            with self.subTest(host=host):
                result=check("https://"+host+"/quote",(host,))
                self.assertEqual(result["status"],"BLOCKED")
                self.assertIn("INVALID_ALLOWLIST",result["blocks"])
                self.assertFalse(result["fetch_allowed"])
    def test_empty_allowlist_blocked(self):
        self.assertIn("INVALID_ALLOWLIST",check("https://data.example.org/",())["blocks"])
    def test_invalid_allowlist_blocked(self):
        self.assertIn("INVALID_ALLOWLIST",check("https://data.example.org/",("DATA.example.org",))["blocks"])
if __name__=="__main__":
    unittest.main()
