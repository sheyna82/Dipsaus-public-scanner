"""Offline SPY capture contract tests; no market requests."""
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from research_capture_spy_history import collect

class Response:
    status=200
    def __init__(self,raw): self.raw=raw
    def __enter__(self): return self
    def __exit__(self,*args): pass
    def read(self,n): return self.raw[:n]

def payload(symbol="SPY", count=101):
    timestamps=[1700000000+i*86400 for i in range(count)]
    quote={k:[100.0+i*.01 for i in range(count)] for k in ("open","high","low","close")}
    quote["volume"]=[1000000]*count
    return json.dumps({"chart":{"result":[{"meta":{"symbol":symbol},"timestamp":timestamps,
        "indicators":{"quote":[quote]}}]}}).encode()

class Tests(unittest.TestCase):
    def test_valid_capture(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"spy.json"
            r=collect(p,fetch=lambda req,timeout:Response(payload()))
            self.assertEqual(r["count"],101)
            d=json.loads(p.read_text())
            self.assertFalse(d["trade_ready"])
            self.assertEqual(d["symbol"],"SPY")
    def test_wrong_symbol(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"symbol_mismatch"):
                collect(Path(td)/"spy.json",fetch=lambda req,timeout:Response(payload("AMD")))
    def test_immutable(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"spy.json"
            p.write_text("existing")
            with self.assertRaises(FileExistsError):
                collect(p,fetch=lambda req,timeout:Response(payload()))
    def test_insufficient(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError,"insufficient"):
                collect(Path(td)/"spy.json",fetch=lambda req,timeout:Response(payload(count=99)))

if __name__=="__main__": unittest.main()
