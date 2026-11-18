"""Read-only adapter from existing US PRE-ALERT handoff to prospective ledger.

A handoff generated_utc is NOT the underlying source observation time.
Never synthesize decision/source timestamps or claim a historical gate failure.
"""
from research.selection_decision_ledger_20261118 import audit_decision_ledger

def audit_us_handoff_ledger_readiness(handoff):
    blocked={"status":"RESEARCH_ONLY_UNATTESTED","trade_ready":False,
             "notify":False,"automatic_orders":False}
    if not isinstance(handoff,dict) or not isinstance(handoff.get("rows"),list):
        return {**blocked,"blocks":["HANDOFF_ROWS_INVALID"],"rows":[]}
    output=[]
    for row in handoff["rows"]:
        if not isinstance(row,dict) or not isinstance(row.get("symbol"),str) or not row["symbol"].strip():
            output.append({"symbol":None,"status":"INVALID_ROW","blocks":["SYMBOL_MISSING"]})
            continue
        missing=[]
        # These fields are not present in the original 2026-11-17 handoff.
        for field in ("discovery_observed_utc","source_daily_last_bar_utc",
                      "source_intraday_last_bar_utc","decision_observed_utc"):
            if not isinstance(row.get(field),str) or not row[field].strip():
                missing.append(field.upper()+"_MISSING")
        if not isinstance(row.get("gates"),dict):
            missing.append("EXPLICIT_GATE_EVIDENCE_MISSING")
        if row.get("execution_ready") is True:
            missing.append("UNVERIFIED_EXECUTION_READY_CLAIM")
        output.append({"symbol":row["symbol"],"status":"PROVENANCE_BLOCKED" if missing else "LEDGER_INPUT_REQUIRES_VALIDATION",
                       "blocks":missing,"research_promotion":row.get("auto_promoted") is True,
                       "structure_confirmed":row.get("structure_quality_pass") is True,
                       "execution_block_count":len(row["execution_blocks"]) if isinstance(row.get("execution_blocks"),list) else None})
    return {**blocked,"handoff_generated_utc":handoff.get("generated_utc"),
            "rows":output,"rows_with_missing_evidence":sum(bool(r["blocks"]) for r in output),
            "note":"Handoff generation time and historical last_bar_date cannot substitute for observed source and decision timestamps."}
