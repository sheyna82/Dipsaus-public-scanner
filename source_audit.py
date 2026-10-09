"""Audit free US ticker lists and independent historical OHLCV endpoints.
This is NOT a full-market scan, real-time quote or trade signal.
"""
import csv
import io
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("reports")
OUT.mkdir(exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; DipsausSourceAudit/0.2)"}
FIELDS = {"Date", "Open", "High", "Low", "Close", "Volume"}


def download(url):
    request = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8-sig")


def ticker_lists():
    sources = {
        "nasdaq": "https://www.nasdaqtrader.com/dynamic/SymDir/nasdaqlisted.txt",
        "other": "https://www.nasdaqtrader.com/dynamic/SymDir/otherlisted.txt",
    }
    results, errors = {}, {}
    for name, url in sources.items():
        try:
            rows = list(csv.DictReader(
                (line for line in download(url).splitlines()
                 if not line.startswith("File Creation Time")), delimiter="|"))
            rows = [r for r in rows if r.get("Test Issue", "N") == "N"
                    and r.get("ETF", "N") == "N"]
            results[name] = {
                "url": url, "preliminary_rows": len(rows),
                "note": "Still includes warrants, units and other non-common-stock instruments.",
            }
        except Exception as exc:
            errors[name] = type(exc).__name__
    return results, errors


def stooq_probe():
    url = "https://stooq.com/q/d/l/?s=aapl.us&i=d"
    try:
        body = download(url)
        rows = list(csv.DictReader(io.StringIO(body)))
        valid = [r for r in rows if FIELDS.issubset(r)
                 and r.get("Date") and r.get("Close") and r.get("Volume")]
        if valid:
            return {"ok": True, "rows": len(valid),
                    "last_date": valid[-1]["Date"]}, None
        # Never expose a token or raw URL containing an API key.
        preview = body.strip()[:180]
        if "apikey" in body.lower():
            reason = "API_KEY_REQUIRED"
        elif body.lstrip().startswith("<"):
            reason = "HTML_OR_CHALLENGE_INSTEAD_OF_CSV"
        elif "N/D" in body:
            reason = "NO_DATA"
        else:
            reason = "UNEXPECTED_RESPONSE"
        return {"ok": False, "reason": reason,
                "response_preview": preview}, None
    except Exception as exc:
        return {"ok": False}, type(exc).__name__


def yahoo_probe():
    # Public chart endpoint: connectivity test only; access/rate limits may change.
    url = "https://query1.finance.yahoo.com/v8/finance/chart/AAPL?range=3mo&interval=1d"
    try:
        data = json.loads(download(url))
        result = data["chart"]["result"][0]
        quote = result["indicators"]["quote"][0]
        valid = sum(1 for c, v in zip(quote["close"], quote["volume"])
                    if c is not None and v is not None)
        if valid < 20:
            return {"ok": False, "reason": "INSUFFICIENT_BARS",
                    "valid_bars": valid}, None
        last = datetime.fromtimestamp(result["timestamp"][-1], timezone.utc)
        return {"ok": True, "valid_bars": valid,
                "last_bar_utc": last.isoformat()}, None
    except Exception as exc:
        return {"ok": False}, type(exc).__name__


def main():
    lists, errors = ticker_lists()
    stooq, stooq_error = stooq_probe()
    yahoo, yahoo_error = yahoo_probe()
    report = {
        "run_utc": datetime.now(timezone.utc).isoformat(),
        "status": "SOURCE_TEST_ONLY",
        "universe": lists,
        "universe_errors": errors,
        "stooq": stooq,
        "stooq_error": stooq_error,
        "yahoo": yahoo,
        "yahoo_error": yahoo_error,
        "actual_symbols_screened": 0,
        "full_us_scan_executed": False,
        "trade_ready": False,
        "warning": "Ticker rows are preliminary. No full OHLCV scan or live execution quote.",
    }
    (OUT / "source_audit.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if errors or not yahoo.get("ok"):
        raise SystemExit("No verified independent free OHLCV fallback; see audit")
    print("PASS: official ticker lists and independent sample OHLCV reachable")


if __name__ == "__main__":
    main()

