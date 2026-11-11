import unittest
from unittest.mock import patch, MagicMock
from research.spoor2_eu_pinned_https_capture_20261111 import capture_pinned_https

class PinnedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            selected_address="8.8.8.8")
    def test_injected_transport_never_authorizes(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**self.args,transport=object())
        self.assertEqual(r["status"],"SIMULATED_TRANSPORT_ONLY")
        self.assertFalse(r["trade_ready"])
        self.assertFalse(r["connection_authorized"])
    def test_private_address_blocks_before_socket(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"selected_address":"127.0.0.1"})
        self.assertEqual(r["status"],"BLOCKED")
    def test_mismatched_address_blocks(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"selected_address":"1.1.1.1"})
        self.assertEqual(r["status"],"BLOCKED")
    def test_disallowed_host_blocks(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"url":"https://evil.test/"})
        self.assertEqual(r["status"],"BLOCKED")
    def test_socket_failure_blocks(self):
        with patch("socket.create_connection",side_effect=OSError("offline")):
            r=capture_pinned_https(**self.args)
        self.assertEqual(r["blocks"],["HTTPS_CAPTURE_FAILED"])
    def test_request_uses_real_crlf_and_validated_tls_peer(self):
        raw=MagicMock()
        raw.getpeername.return_value=("8.8.8.8",443)
        tls=MagicMock()
        tls.getpeername.return_value=("8.8.8.8",443)
        response=MagicMock()
        response.status=200
        response.getheader.return_value="identity"
        response.read.return_value=b"evidence"
        with (patch("socket.create_connection",return_value=raw),
             patch("ssl.create_default_context") as ctx,
             patch("http.client.HTTPResponse",return_value=response)):
            ctx.return_value.wrap_socket.return_value=tls
            r=capture_pinned_https(**self.args)
        self.assertEqual(r["status"],"HTTPS_CAPTURED_READ_ONLY")
        sent=tls.sendall.call_args.args[0]
        self.assertIn(b"GET /prices HTTP/1.1\\r\\nHost: data.example.org\\r\\n",sent)
        self.assertTrue(sent.endswith(b"\\r\\n\\r\\n"))
        self.assertNotIn(b"\\\\r\\\\n",sent)
        self.assertFalse(r["trade_ready"])
    def test_tls_peer_switch_blocks(self):
        raw=MagicMock()
        raw.getpeername.return_value=("8.8.8.8",443)
        tls=MagicMock()
        tls.getpeername.return_value=("1.1.1.1",443)
        with (patch("socket.create_connection",return_value=raw),
             patch("ssl.create_default_context") as ctx):
            ctx.return_value.wrap_socket.return_value=tls
            r=capture_pinned_https(**self.args)
        self.assertEqual(r["blocks"],["TLS_SOCKET_PEER_MISMATCH"])
    def test_resource_limits_block(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"max_response_bytes":0})
        self.assertEqual(r["status"],"BLOCKED")
if __name__=="__main__": unittest.main()
