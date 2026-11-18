"""Offline selection-effectiveness audit for US PRE-ALERT handoff.

Counts distinct stages without equating a research block to a bad trade.
No provider calls, private data, notifications, orders or production writes.
"""
from collections import Counter

def audit_selection_handoff(report):
    if not isinstance(report,dict) or not isinstance(report.get("rows"),list):
        return {"status":"INVALID_INPUT","blocks":["ROWS_MISSING"],"trade_ready":False,"notify":False,"automatic_orders":False}
    counts=Counter()
    reasons=Counter()
    lanes=Counter()
    symbols=set()
    duplicate_symbols=set()
    invalid_rows=0
    for row in report["rows"]:
        if not isinstance(row,dict) or not isinstance(row.get("symbol"),str) or not row["symbol"].strip():
            invalid_rows+=1
            continue
        symbol=row["symbol"]
        if symbol in symbols:
            duplicate_symbols.add(symbol)
        symbols.add(symbol)
        lanes[str(row.get("discovery_lane") or "UNKNOWN")]+=1
        counts["discovered_handoff_rows"]+=1
        if row.get("auto_promoted") is True:
            counts["prealert_promoted_rows"]+=1
        if row.get("structure_quality_pass") is True:
            counts["intraday_structure_confirmed_rows"]+=1
        if row.get("execution_ready") is True:
            counts["execution_ready_claims"]+=1
        blocks=row.get("execution_blocks")
        if not isinstance(blocks,list):
            reasons["EXECUTION_BLOCKS_MISSING_OR_INVALID"]+=1
        else:
            for block in set(x for x in blocks if isinstance(x,str) and x):
                reasons[block]+=1
    issues=[]
    if invalid_rows:issues.append("INVALID_ROWS")
    if duplicate_symbols:issues.append("DUPLICATE_SYMBOLS")
    if counts["execution_ready_claims"]:issues.append("UNVERIFIED_EXECUTION_READY_CLAIMS")
    return {"status":"RESEARCH_ONLY","counts":dict(sorted(counts.items())),
            "lanes":dict(sorted(lanes.items())),
            "execution_block_frequency":dict(sorted(reasons.items())),
            "invalid_row_count":invalid_rows,
            "duplicate_symbol_count":len(duplicate_symbols),
            "issues":issues,
            "interpretation":"Blocks indicate pending evidence, not proven unattractive opportunities; no counterfactual outcomes inferred.",
            "trade_ready":False,"notify":False,"automatic_orders":False}
