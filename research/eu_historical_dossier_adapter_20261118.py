"""Read-only EU historical candidate dossier readiness audit.

Existing Spoor 2 historical bridge consumes candidate symbol/recovery_map and
last_close_usd, but those fields cannot prove an EU quote, an observed timestamp,
or an actual decision. No currency inference or ledger backfill.
"""

def audit_eu_historical_dossier_readiness(report):
    base={"status":"RESEARCH_ONLY_UNATTESTED","trade_ready":False,
          "notify":False,"automatic_orders":False}
    if not isinstance(report,dict) or not isinstance(report.get("candidates"),list):
        return {**base,"blocks":["HISTORICAL_CANDIDATES_INVALID"],"rows":[]}
    rows=[]
    for c in report["candidates"]:
        if not isinstance(c,dict) or not isinstance(c.get("symbol"),str) or not c["symbol"].strip():
            rows.append({"symbol":None,"blocks":["SYMBOL_MISSING"],"ledger_ready":False})
            continue
        missing=[]
        if c.get("market")!="EU":missing.append("EU_MARKET_NOT_ATTESTED")
        if c.get("quote_currency") not in ("EUR","GBP","GBp","SEK","NOK","DKK","CHF"):
            missing.append("EU_QUOTE_UNIT_NOT_ATTESTED")
        for k in ("source_observed_utc","decision_observed_utc","decision_stage","explicit_gate_evidence"):
            if c.get(k) is None:missing.append(k.upper()+"_MISSING")
        if c.get("trade_ready") is True:missing.append("UNVERIFIED_TRADE_READY_CLAIM")
        rows.append({"symbol":c["symbol"],"blocks":missing,"ledger_ready":False,
                     "historical_recovery_map_present":isinstance(c.get("recovery_map"),dict),
                     "quote_unit":c.get("quote_currency")})
    return {**base,"rows":rows,
            "rows_with_missing_evidence":sum(bool(x["blocks"]) for x in rows),
            "note":"Historical recovery_map and last_close_usd are not EU executable quote or point-in-time decisions."}
