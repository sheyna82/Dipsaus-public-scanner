"""Two-year public-history research probe, isolated from live scanner.

Reuses the frozen event rule. Data quality, split adjustments and earnings
remain unverified; outputs are descriptive and never trading instructions.
"""
import json
from urllib.request import Request, urlopen
from research_probe_alternative_daily_source import BASE, SYMBOLS
from research_four_event_history_results import evaluate_payload

LONG_BASE = BASE.replace("range=3mo", "range=2y")


def evaluate_long_symbol(symbol, fetch=None):
    if symbol not in SYMBOLS:
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "unapproved_symbol"}
    try:
        url = LONG_BASE.format(symbol=symbol)
        if fetch is None:
            with urlopen(Request(url, headers={"User-Agent": "Mozilla/5.0"}),
                         timeout=12) as response:
                raw = response.read(900_001)
        else:
            raw = fetch(url)
        if len(raw) > 900_000:
            return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "oversized"}
        out = evaluate_payload(symbol, json.loads(raw))
        if out.get("status") == "DESCRIPTIVE_HISTORY":
            out["long_history_research_only"] = True
            out["adjustments_independently_verified"] = False
            out["predictive_edge_proven"] = False
            out["trade_ready"] = False
        return out
    except (OSError, ValueError, TimeoutError, UnicodeError, TypeError):
        return {"symbol": symbol, "status": "DATA_BLOCKED", "reason": "fetch_failed"}


if __name__ == "__main__":
    for symbol in SYMBOLS:
        result = evaluate_long_symbol(symbol)
        # Avoid huge log lines; print just key diagnostics.
        holdout = result.get("chronological_holdout", {})
        print(json.dumps({"symbol": symbol, "status": result.get("status"),
                          "history_bars": result.get("history_bars"),
                          "signal_count": result.get("signal_count"),
                          "holdout": holdout,
                          "adjustments_independently_verified": False,
                          "predictive_edge_proven": False, "trade_ready": False},
                         sort_keys=True))
