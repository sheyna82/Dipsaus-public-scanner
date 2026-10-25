"""Research-only prospective batch candidates from verified-shaped daily close rows.

Requires four consecutive *common* sessions per symbol and benchmark. Gaps in
the two sources are not silently filled. No external fetch or live writes.
"""
from datetime import date
from research_prospective_signal_ledger import build_candidate


def generate_prospective_batch(stock_rows_by_symbol, spy_rows, *, signal_session):
    date.fromisoformat(signal_session)
    spy_map = {r["date"]: r["close"] for r in spy_rows}
    if len(spy_map) != len(spy_rows):
        raise ValueError("duplicate_spy_session")
    results = []
    for symbol in ("COHU", "AMD", "META"):
        stock_rows = stock_rows_by_symbol.get(symbol)
        if stock_rows is None:
            results.append({"symbol": symbol, "status": "missing_symbol_data"})
            continue
        stock_map = {r["date"]: r["close"] for r in stock_rows}
        if len(stock_map) != len(stock_rows):
            results.append({"symbol": symbol, "status": "duplicate_stock_session"})
            continue
        if signal_session not in spy_map or signal_session not in stock_map:
            results.append({"symbol": symbol, "status": "missing_signal_session"})
            continue
        # Use the benchmark's last four sessions to identify gaps in stock data.
        benchmark_sessions = sorted(day for day in spy_map if day <= signal_session)
        if len(benchmark_sessions) < 4:
            results.append({"symbol": symbol, "status": "insufficient_benchmark_history"})
            continue
        sessions = benchmark_sessions[-4:]
        if any(day not in stock_map for day in sessions):
            results.append({"symbol": symbol, "status": "missing_stock_trading_session"})
            continue
        record = build_candidate(symbol, signal_session,
                                 [stock_map[day] for day in sessions],
                                 [spy_map[day] for day in sessions])
        record["input_sessions"] = sessions
        results.append({"symbol": symbol, "status": "candidate", "record": record})
    return {"signal_session": signal_session, "research_only": True,
            "trade_ready": False, "results": results}
