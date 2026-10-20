"""Separate discovery-universe accounting; never confuse discovery with manual watch coverage."""
from datetime import datetime, timezone
from candidate_coverage_audit import reconcile

def _checked(report, timestamp_key, universe_key, observed_key, failures_key=None, *, now=None):
    if not isinstance(report, dict):
        raise ValueError("discovery report missing")
    stamp=report.get(timestamp_key)
    if not isinstance(stamp,str):
        raise ValueError("discovery timestamp missing")
    universe=report.get(universe_key)
    if not isinstance(universe,list) or len(universe)!=len(set(universe)) or any(not isinstance(x,str) or not x for x in universe):
        raise ValueError("discovery universe invalid")
    observed=report.get(observed_key)
    if not isinstance(observed,list):
        raise ValueError("discovery observations invalid")
    failures=report.get(failures_key,{}) if failures_key else {}
    if not isinstance(failures,dict):
        raise ValueError("discovery failures invalid")
    seen=set()
    for row in observed:
        if not isinstance(row,dict) or not isinstance(row.get("symbol"),str):
            raise ValueError("invalid discovery observation")
        seen.add(row["symbol"])
    if not seen.issubset(set(universe)) or not set(failures).issubset(set(universe)):
        raise ValueError("unregistered discovery symbol")
    observations=[]
    for symbol in universe:
        if symbol in seen:
            observations.append({"candidate_id":symbol,"status":"FRESH_CHECKED","checked_at":stamp})
        elif symbol in failures:
            observations.append({"candidate_id":symbol,"status":"DATA_BLOCKED","reason":"PROVIDER_FAILED","checked_at":stamp})
    return reconcile([{"id":x,"status":"ACTIVE"} for x in universe],observations,now=now)

def audit_us_batch(report, *, now=None):
    """US sample_symbols are selected universe, not just promoted candidates."""
    if not isinstance(report, dict) or not isinstance(report.get("sample_symbols"), list):
        raise ValueError("US report or sample missing")
    if report.get("requested_symbols")!=len(report["sample_symbols"]):
        raise ValueError("US batch selection count mismatch")
    if report.get("actual_symbols_screened")!=(
        report.get("requested_symbols",0)-len(report.get("failures",{}))):
        raise ValueError("US screened/failure count mismatch")
    selected=report.get("sample_symbols")
    if not isinstance(selected,list) or len(selected)!=len(set(selected)):
        raise ValueError("US sample invalid")
    if not selected:
        return {"selected":0,"screened_count_only":0,"provider_failures":0,
                "per_symbol_screened_proof":False,"complete":False,
                "all_data_available":False,"reason":"US_EMPTY_BATCH_NO_COVERAGE_PROOF"}
    failures=report.get("failures",{})
    screened=report.get("screened_symbols")
    if not isinstance(failures,dict) or not set(failures).issubset(set(selected)):
        raise ValueError("US failures invalid")
    if any(not isinstance(x,str) or not x for x in selected):
        raise ValueError("US sample symbol invalid")
    if report.get("batch_index") is not None and (not isinstance(report["batch_index"],int) or not 0 <= report["batch_index"] < 21):
        raise ValueError("US batch index invalid")
    if screened is None:
        return {"selected":len(selected),"screened_count_only":report["actual_symbols_screened"],
                "provider_failures":len(failures),"per_symbol_screened_proof":False,
                "complete":False,"reason":"US_NONPROMOTED_SCREENED_SYMBOLS_NOT_PERSISTED"}
    if not isinstance(screened,list) or len(screened)!=len(set(screened)):
        raise ValueError("US screened symbols invalid")
    if len(screened)!=report["actual_symbols_screened"] or (
        set(screened)|set(failures))!=set(selected) or set(screened)&set(failures):
        raise ValueError("US per-symbol reconciliation mismatch")
    promoted=report.get("candidates",[])
    if not isinstance(promoted,list) or any(not isinstance(x,dict) or x.get("symbol") not in screened for x in promoted):
        raise ValueError("US promoted candidates invalid")
    return {"selected":len(selected),"screened_count_only":len(screened),
            "provider_failures":len(failures),"per_symbol_screened_proof":True,
            "complete":True,"all_data_available":len(failures)==0,
            "reason":"US_BATCH_SYMBOLS_RECONCILED_WITH_BLOCKERS" if failures else "US_BATCH_SYMBOLS_RECONCILED"}

def audit_eu_pipeline(history, intraday, quotes, joined):
    """Reconcile EU eligible watchlist across every stage; never claim market-wide coverage."""
    reports = (history, intraday, quotes, joined)
    if any(not isinstance(r, dict) for r in reports):
        raise ValueError("EU stage report missing")

    def symbols(report):
        rows = report.get("candidates")
        if not isinstance(rows, list):
            raise ValueError("EU stage candidates missing")
        names = [r.get("symbol") for r in rows if isinstance(r, dict)]
        if (len(names) != len(rows) or
                any(not isinstance(x, str) or not x for x in names) or
                len(set(names)) != len(names)):
            raise ValueError("EU stage symbols invalid or duplicate")
        return set(names)

    historical = symbols(history)
    eligible = {r["symbol"] for r in history["candidates"] if r.get("discovery_eligible")}
    intraday_symbols = symbols(intraday)
    quote_symbols = symbols(quotes)
    joined_symbols = symbols(joined)

    if not intraday_symbols.issubset(historical):
        raise ValueError("EU intraday includes unknown historical symbol")
    if not quote_symbols.issubset(intraday_symbols) or not joined_symbols.issubset(intraday_symbols):
        raise ValueError("EU downstream includes unknown symbol")
    if intraday.get("watchlist_eligible_count") != len(eligible):
        raise ValueError("EU eligible count mismatch")
    if intraday.get("checked_count") != len(intraday_symbols):
        raise ValueError("EU intraday count mismatch")
    if quotes.get("checked") != len(quote_symbols):
        raise ValueError("EU quote count mismatch")
    if joined.get("joined_count") != len(joined_symbols):
        raise ValueError("EU joined count mismatch")

    intraday_blocked = sum(
        row.get("data_status") != "INTRADAY-RESEARCH-ONLY"
        for row in intraday["candidates"])
    quote_blocked = sum(
        row.get("provider_freshness_class") in ("DATA-BLOCKED", "NO-VALID-QUOTE",
                                                "STALE-OR-TIMESTAMP-INVALID")
        or "QUOTE-DATA-BLOCKED" in (row.get("execution_blocks") or [])
        for row in quotes["candidates"])
    selection_nonempty = bool(eligible)
    missing_intraday = eligible - intraday_symbols
    missing_quote = intraday_symbols - quote_symbols
    missing_joined = intraday_symbols - joined_symbols
    return {
        "eligible": len(eligible),
        "intraday": len(intraday_symbols),
        "quote": len(quote_symbols),
        "joined": len(joined_symbols),
        "missing_intraday": len(missing_intraday),
        "missing_quote": len(missing_quote),
        "missing_joined": len(missing_joined),
        "intraday_blocked": intraday_blocked,
        "quote_blocked": quote_blocked,
        "complete": selection_nonempty and not (missing_intraday or missing_quote or missing_joined),
        "all_data_available": selection_nonempty and not (missing_intraday or missing_quote or missing_joined or
                                   intraday_blocked or quote_blocked),
        "scope": "EU_DISCOVERY_ELIGIBLE_ONLY",
        "selection_nonempty": selection_nonempty,
    }


def audit_eu_joined(report, *, now=None):
    """EU joined candidates alone do not prove the whole upstream universe."""
    if not isinstance(report,dict) or not isinstance(report.get("candidates"),list):
        raise ValueError("EU joined report invalid")
    rows=report["candidates"]
    symbols=[r.get("symbol") for r in rows if isinstance(r,dict)]
    if len(symbols)!=len(rows) or len(symbols)!=len(set(symbols)) or any(not isinstance(x,str) or not x for x in symbols):
        raise ValueError("EU joined symbols invalid")
    if report.get("joined_count")!=len(rows):
        raise ValueError("EU joined count mismatch")
    return {"joined":len(rows),"upstream_universe":report.get("historical_universe"),
            "complete":False,"reason":"EU_UPSTREAM_UNIVERSE_NOT_RECONCILED"}
