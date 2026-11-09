"""Offline fail-closed verification of preserved Yahoo benchmark raw responses.

Checks that captured bars and metadata are exactly reproducible from retained
provider bytes. Does NOT certify provider-to-official-index identity.
"""
import base64
import binascii
import hashlib
import json
import math
from pathlib import Path

from research_capture_europe_benchmarks import BENCHMARKS, audit_omxh25_daily_bar

def verify_capture(document):
    if (not isinstance(document, dict) or document.get("schema") != "dipsaus_europe_benchmark_research_v1"
            or document.get("research_only") is not True or document.get("trade_ready") is not False
            or document.get("benchmark_identity_verified") is not False):
        raise ValueError("BENCHMARK_CAPTURE_GATE_INVALID")
    series = document.get("series")
    if not isinstance(series, dict) or set(series) != set(BENCHMARKS):
        raise ValueError("BENCHMARK_SERIES_INVALID")
    for name, symbol in BENCHMARKS.items():
        entry = series[name]
        if not isinstance(entry, dict):
            raise ValueError("BENCHMARK_ENTRY_INVALID")
        encoded = entry.get("source_raw_base64")
        if not isinstance(encoded, str):
            raise ValueError("BENCHMARK_RAW_MISSING")
        try:
            raw = base64.b64decode(encoded, validate=True)
        except (ValueError, binascii.Error) as exc:
            raise ValueError("BENCHMARK_RAW_BASE64_INVALID") from exc
        if not raw or len(raw) > 2_000_000 or hashlib.sha256(raw).hexdigest() != entry.get("source_sha256"):
            raise ValueError("BENCHMARK_RAW_HASH_MISMATCH")
        try:
            parsed = json.loads(raw, parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")))
            data = parsed["chart"]["result"][0]
            meta = data["meta"]
            timestamps = data["timestamp"]
            closes = data["indicators"]["quote"][0]["close"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ValueError("BENCHMARK_RAW_SCHEMA_INVALID") from exc
        if (meta.get("symbol") != symbol or meta.get("currency") != "EUR"
                or meta.get("instrumentType") != "INDEX"
                or entry.get("provider_symbol") != symbol):
            raise ValueError("BENCHMARK_PROVIDER_IDENTITY_CONFLICT")
        fields = ("symbol", "shortName", "longName", "currency", "instrumentType", "exchangeName", "timezone", "gmtoffset")
        if entry.get("provider_metadata") != {key: meta.get(key) for key in fields}:
            raise ValueError("BENCHMARK_METADATA_MISMATCH")
        if len(timestamps) != len(closes):
            raise ValueError("BENCHMARK_RAW_LENGTH_MISMATCH")
        bars = []
        for t, close in zip(timestamps, closes):
            if close is None or isinstance(close, bool) or not isinstance(close, (int, float)) or not math.isfinite(close) or close <= 0:
                continue
            bars.append({"t": int(t), "close": close})
        if (len(bars) < 100 or any(a["t"] >= b["t"] for a, b in zip(bars, bars[1:]))
                or bars != entry.get("bars") or len(bars) != entry.get("count")):
            raise ValueError("BENCHMARK_BARS_MISMATCH")
        if name == "OMXH25":
            audits = [audit_omxh25_daily_bar(bar) for bar in bars]
            consistent = sum(a["session_open_label_consistent"] for a in audits)
            expected = {
                "schema": "omxh25_helsinki_label_audit_v1",
                "bars_sha256": hashlib.sha256(json.dumps(bars, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest(),
                "checked": len(audits), "consistent": consistent,
                "inconsistent_dates": [a["session_date"] for a in audits if not a["session_open_label_consistent"]],
                "research_only": True, "identity_approved": False,
                "validation_status": "blocked" if consistent != len(audits) else "consistent_unverified",
                "blocks_identity_review": True
            }
            if entry.get("daily_label_audit") != expected:
                raise ValueError("BENCHMARK_LABEL_AUDIT_MISMATCH")
    return {"status": "provider_bytes_reconciled", "series_count": len(series),
            "benchmark_identity_verified": False, "research_only": True, "trade_ready": False}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("capture_json")
    args = parser.parse_args()
    print(json.dumps(verify_capture(json.loads(Path(args.capture_json).read_text())), sort_keys=True))
