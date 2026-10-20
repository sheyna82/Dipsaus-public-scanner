"""Offline, network-free checks for US discovery diagnostics."""
import io
import json
import unittest
from unittest.mock import patch

import us_momentum_recovery_discovery as discovery


class DiscoveryNetworkAuditTests(unittest.TestCase):
    def setUp(self):
        discovery.NETWORK_AUDIT.update(requests=0, failures=0, elapsed_s=0.0, slow_requests=0)

    def test_bounded_map_preserves_order_and_coverage(self):
        values=list(range(23))
        result=list(discovery.ordered_bounded_map(lambda x: x*x, values, workers=3, window=5))
        self.assertEqual(result,[x*x for x in values])

    def test_bounded_map_rejects_invalid_limits(self):
        with self.assertRaises(ValueError):
            list(discovery.ordered_bounded_map(lambda x:x,[1],workers=5,window=4))

    def test_success_is_counted_without_logging_response(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return b'{"private": "do-not-print"}'
        with patch.object(discovery.urllib.request, "urlopen", return_value=Response()) as opener:
            with patch.object(discovery.time, "monotonic", side_effect=[10.0, 10.4]):
                result = discovery.get_json("https://example.invalid/private")
        self.assertEqual(result["private"], "do-not-print")
        self.assertEqual(discovery.NETWORK_AUDIT["requests"], 1)
        self.assertEqual(discovery.NETWORK_AUDIT["failures"], 0)
        self.assertAlmostEqual(discovery.NETWORK_AUDIT["elapsed_s"], 0.4)
        self.assertEqual(discovery.NETWORK_AUDIT["slow_requests"], 0)
        self.assertEqual(opener.call_args.kwargs["timeout"], 15)

    def test_timeout_is_counted_and_propagated(self):
        with patch.object(discovery.urllib.request, "urlopen", side_effect=TimeoutError("private url")):
            with patch.object(discovery.time, "monotonic", side_effect=[10.0, 16.0]):
                with self.assertRaises(TimeoutError):
                    discovery.get_json("https://example.invalid/private")
        self.assertEqual(discovery.NETWORK_AUDIT["requests"], 1)
        self.assertEqual(discovery.NETWORK_AUDIT["failures"], 1)
        self.assertEqual(discovery.NETWORK_AUDIT["slow_requests"], 1)
        self.assertAlmostEqual(discovery.NETWORK_AUDIT["elapsed_s"], 6.0)


if __name__ == "__main__":
    unittest.main()
