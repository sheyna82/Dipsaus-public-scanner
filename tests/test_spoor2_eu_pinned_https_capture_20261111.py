import unittest
from unittest.mock import patch, MagicMock
from research.spoor2_eu_pinned_https_capture_20261111 import capture_pinned_https

class PinnedCaptureTests(unittest.TestCase):
    def setUp(self):
        self.args=dict(network_enabled=True,url="https://data.example.org/prices",
            allowed_hosts=["data.example.org"],resolved_addresses=["8.8.8.8"],
            selected_address="8.8.8.8")
    def test_network_disabled_by_default_even_for_valid_inputs(self):
        args={k:v for k,v in self.args.items() if k!="network_enabled"}
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**args)
        self.assertEqual(r["blocks"],["NETWORK_DISABLED_BY_DEFAULT"])
        self.assertFalse(r["trade_ready"])
    def test_non_boolean_opt_in_never_enables_network(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"network_enabled":1})
        self.assertEqual(r["blocks"],["NETWORK_DISABLED_BY_DEFAULT"])
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
        response.msg.get_all.return_value=["8"]
        response.chunked=False
        response.length=0
        response.getheader.side_effect=lambda name, default=None: "identity" if name=="Content-Encoding" else default
        response.read.return_value=b"evidence"
        with (patch("socket.create_connection",return_value=raw),
             patch("ssl.create_default_context") as ctx,
             patch("http.client.HTTPResponse",return_value=response)):
            ctx.return_value.wrap_socket.return_value=tls
            r=capture_pinned_https(**self.args)
        self.assertEqual(r["status"],"HTTPS_CAPTURED_READ_ONLY")
        sent=tls.sendall.call_args.args[0]
        self.assertIn(b"GET /prices HTTP/1.1\r\nHost: data.example.org\r\n",sent)
        self.assertTrue(sent.endswith(b"\r\n\r\n"))
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
    def _mock_response(self, *, status=200, encoding="identity", body=b"evidence", error=None):
        raw=MagicMock()
        raw.getpeername.return_value=("8.8.8.8",443)
        tls=MagicMock()
        tls.getpeername.return_value=("8.8.8.8",443)
        response=MagicMock()
        response.status=status
        response.msg.get_all.return_value=[str(len(body))]
        response.chunked=False
        response.length=0
        response.getheader.side_effect=lambda name, default=None: encoding if name=="Content-Encoding" else default
        response.read.return_value=body
        if error is not None:
            response.read.side_effect=error
        with (patch("socket.create_connection",return_value=raw),
              patch("ssl.create_default_context") as ctx,
              patch("http.client.HTTPResponse",return_value=response)):
            ctx.return_value.wrap_socket.return_value=tls
            return capture_pinned_https(**self.args)
    def test_http_redirect_rejected(self):
        r=self._mock_response(status=302)
        self.assertEqual(r["blocks"],["UNEXPECTED_HTTP_STATUS"])
    def test_compressed_body_rejected(self):
        r=self._mock_response(encoding="gzip")
        self.assertEqual(r["blocks"],["UNSUPPORTED_CONTENT_ENCODING"])
    def test_oversized_body_rejected(self):
        r=self._mock_response(body=b"x"*(1048576+1))
        self.assertEqual(r["blocks"],["RESPONSE_SIZE_EXCEEDED"])
    def test_truncated_response_exception_blocks(self):
        import http.client
        r=self._mock_response(error=http.client.IncompleteRead(b"partial",12))
        self.assertEqual(r["blocks"],["HTTPS_CAPTURE_FAILED"])
    def test_invalid_certificate_blocks(self):
        import ssl
        with patch("socket.create_connection") as connect, patch("ssl.create_default_context") as ctx:
            connect.return_value.getpeername.return_value=("8.8.8.8",443)
            ctx.return_value.wrap_socket.side_effect=ssl.SSLCertVerificationError("bad cert")
            r=capture_pinned_https(**self.args)
        self.assertEqual(r["blocks"],["HTTPS_CAPTURE_FAILED"])
    def test_missing_content_length_blocks(self):
        with patch("http.client.HTTPResponse") as response:
            response.return_value.msg.get_all.return_value=[]
            response.return_value.status=200
            response.return_value.getheader.side_effect=lambda name,default=None: "identity" if name=="Content-Encoding" else default
            with patch("socket.create_connection") as connect, patch("ssl.create_default_context") as ctx:
                connect.return_value.getpeername.return_value=("8.8.8.8",443)
                ctx.return_value.wrap_socket.return_value.getpeername.return_value=("8.8.8.8",443)
                r=capture_pinned_https(**self.args)
        self.assertEqual(r["blocks"],["UNTRUSTED_RESPONSE_FRAMING"])
    def test_conflicting_content_lengths_block(self):
        r=self._mock_response_with_framing(["8","9"])
        self.assertEqual(r["blocks"],["UNTRUSTED_RESPONSE_FRAMING"])
    def test_truncated_body_without_exception_blocks(self):
        r=self._mock_response_with_framing(["10"],body=b"short")
        self.assertEqual(r["blocks"],["INCOMPLETE_RESPONSE_BODY"])
    def test_invalid_content_length_blocks(self):
        r=self._mock_response_with_framing(["eight"])
        self.assertEqual(r["blocks"],["UNTRUSTED_RESPONSE_FRAMING"])
    def test_chunked_body_blocks(self):
        r=self._mock_response_with_framing(["8"],chunked=True)
        self.assertEqual(r["blocks"],["UNTRUSTED_RESPONSE_FRAMING"])
    def _mock_response_with_framing(self,lengths,body=b"evidence",chunked=False):
        raw=MagicMock()
        raw.getpeername.return_value=("8.8.8.8",443)
        tls=MagicMock()
        tls.getpeername.return_value=("8.8.8.8",443)
        response=MagicMock()
        response.status=200
        response.getheader.side_effect=lambda name,default=None: "identity" if name=="Content-Encoding" else default
        response.msg.get_all.return_value=lengths
        response.chunked=chunked
        response.length=0
        response.read.return_value=body
        with (patch("socket.create_connection",return_value=raw),
              patch("ssl.create_default_context") as ctx,
              patch("http.client.HTTPResponse",return_value=response)):
            ctx.return_value.wrap_socket.return_value=tls
            return capture_pinned_https(**self.args)
    def test_resource_limits_block(self):
        with patch("socket.create_connection",side_effect=AssertionError("network forbidden")):
            r=capture_pinned_https(**{**self.args,"max_response_bytes":0})
        self.assertEqual(r["status"],"BLOCKED")
if __name__=="__main__": unittest.main()
