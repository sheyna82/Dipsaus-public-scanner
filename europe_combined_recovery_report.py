"""Combine historical, 15m and 1m audits. Delayed provider data may request a broker look-now, never an execution signal."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path("reports")
def load(name):return json.loads((ROOT/name).read_text())
def main():
    history=load("europe_swing_research.json");intraday=load("europe_intraday_confirmation.json");quotes=load("europe_quote_execution_audit.json")
    by_history={r["symbol"]:r for r in history["candidates"]};by_quote={r["symbol"]:r for r in quotes["candidates"]};rows=[]
    for item in intraday["candidates"]:
        sym=item["symbol"];h=by_history[sym];q=by_quote.get(sym,{});flags=h.get("research_flags",[])
        recovery_score=item.get("early_recovery_score")
        if recovery_score is None:recovery_score=sum((item.get("higher_last_low") is True,item.get("above_prior_bar_high") is True))
        min_structure=item.get("minimum_structure_score",2)
        structure=recovery_score>=min_structure;quote_fresh=q.get("provider_freshness_pass") is True;quote_delayed=q.get("provider_delayed_but_usable_for_attention") is True
        evidence="EARLY-STRUCTURE-OBSERVED" if structure else "NO-COMBINED-15M-CONFIRMATION"
        if item.get("data_status")!="INTRADAY-RESEARCH-ONLY":evidence="INTRADAY-DATA-BLOCKED"
        scenarios=h.get("historical_3500_eur_scenarios") or {};rr=scenarios.get("rr_to_meaningful");rr_further=scenarios.get("rr_to_further");gross=scenarios.get("meaningful_resistance_gross_eur");gross_further=scenarios.get("further_zone_gross_eur")
        passage_review=("RR-BELOW-2-TO-1-AT-FIRST-MEANINGFUL; FURTHER-ZONE-REQUIRES-PASSAGE-VALIDATION" in flags)
        money_pass=(rr is not None and rr>=2 and gross is not None and gross>=150);money_review=(passage_review and rr_further is not None and rr_further>=2 and gross_further is not None and gross_further>=150)
        stale="STALE-DATA" in flags;meaningful_unresolved="MEANINGFUL-RESISTANCE-UNRESOLVED" in flags
        early_watch=bool(structure and not stale and h.get("discovery_eligible",True));broker_candidate=bool(early_watch and not meaningful_unresolved and (money_pass or money_review))
        # Key distinction: delayed EU data must not silently bury a good setup. It may
        # request an immediate DEGIRO look, but ONLY the broker quote can validate entry.
        broker_verify_now=bool(broker_candidate and (quote_fresh or quote_delayed))
        provider_live_handoff=bool(broker_candidate and quote_fresh)
        if provider_live_handoff:
            prealert_status="DEGIRO-CHECK-NOW";prealert_reason="Fresh provider evidence + recovery/money gates. Verify current DEGIRO bid/ask, news/events, portfolio fit and re-run R/R on broker price; provider price is not executable."
        elif broker_verify_now:
            prealert_status="DEGIRO-VERIFY-NOW-DELAYED-PROVIDER";prealert_reason="Recovery/money gates are interesting and the provider feed is delayed but still recent enough for attention. Open DEGIRO NOW to obtain the current price/bid-ask and verify the setup; never execute from the delayed provider price."
        elif broker_candidate:
            prealert_status="BROKER-CHECK-CANDIDATE";prealert_reason="Recovery/money gates are interesting, but provider evidence is too stale for urgency. Keep on radar; do not execute from this quote."
        elif early_watch:
            prealert_status="EARLY-RECOVERY-WATCH";prealert_reason="Recovery structure is visible, but resistance/RR or another execution input is unresolved. Keep researching; do not execute."
        else:prealert_status="WATCH/RESEARCH";prealert_reason=None
        rows.append({"symbol":sym,"sector":h.get("sector"),"currency":h.get("currency"),"historical_close":h.get("historical_close"),"drawdown_126d_pct":h.get("drawdown_126d_pct"),"historical_status":h.get("status"),"historical_flags":flags,"historical_execution_blockers":h.get("execution_blockers",[]),"discovery_eligible":h.get("discovery_eligible"),"historical_profit_reference_under_150_eur":h.get("advisory_under_150_eur_reference",False),"historical_3500_eur_scenarios":h.get("historical_3500_eur_scenarios"),"historical_first_friction":h.get("first_friction"),"historical_meaningful_resistance":h.get("first_meaningful_resistance"),"historical_further_zone":h.get("further_recovery_zone"),"intraday_evidence":evidence,"last_15m_bar":(item.get("latest_bar") or {}).get("time"),"higher_last_low":item.get("higher_last_low"),"above_prior_bar_high":item.get("above_prior_bar_high"),"holding_recent_low":item.get("holding_recent_low"),"reclaim_recent_range":item.get("reclaim_recent_range"),"early_recovery_score":recovery_score,"session_phase":item.get("session_phase"),"minimum_structure_score":min_structure,"provider_1m_quote":q.get("quote_close"),"provider_1m_quote_utc":q.get("quote_utc"),"provider_quote_age_seconds_at_run":q.get("quote_age_seconds"),"provider_freshness_class":q.get("provider_freshness_class"),"provider_freshness_pass":quote_fresh,"provider_delayed_but_usable_for_attention":quote_delayed,"provider_bid":q.get("provider_bid"),"provider_ask":q.get("provider_ask"),"provider_spread_pct":q.get("provider_spread_pct"),"execution_blocks":q.get("execution_blocks",["QUOTE-AUDIT-MISSING"]),"early_recovery_watch":early_watch,"broker_check_candidate":broker_candidate,"broker_verify_now":broker_verify_now,"degiro_check":provider_live_handoff,"degiro_check_now":provider_live_handoff,"prealert_status":prealert_status,"prealert_reason":prealert_reason,"portfolio_fit_verified":False,"broker_quote_verified":False,"trade_ready":False})
    data_blocked=[r["symbol"] for r in rows if r.get("intraday_evidence")=="INTRADAY-DATA-BLOCKED" or r.get("provider_freshness_class") in ("DATA-BLOCKED","NO-VALID-QUOTE")]
    structure_unverified=[r["symbol"] for r in rows if r.get("intraday_evidence")=="EARLY-STRUCTURE-OBSERVED" and r.get("provider_freshness_class") in ("DATA-BLOCKED","NO-VALID-QUOTE","STALE-OR-TIMESTAMP-INVALID")]
    urgent=[r["symbol"] for r in rows if r.get("broker_verify_now")];fresh=[r["symbol"] for r in rows if r.get("degiro_check_now")];delayed=[r["symbol"] for r in rows if r.get("broker_verify_now") and not r.get("degiro_check_now")]
    result={"generated_utc":datetime.now(timezone.utc).isoformat(),"scope":"Joined research/provider evidence. Fresh OR recent-delayed provider evidence can request DEGIRO verification; only broker data can validate execution.","historical_universe":history.get("stored_symbols_examined"),"early_watchlist_eligible":intraday.get("watchlist_eligible_count"),"joined_count":len(rows),"early_recovery_watch_count":sum(1 for r in rows if r.get("early_recovery_watch")),"early_recovery_watch_symbols":[r["symbol"] for r in rows if r.get("early_recovery_watch")],"broker_check_candidate_count":sum(1 for r in rows if r.get("broker_check_candidate")),"broker_check_candidate_symbols":[r["symbol"] for r in rows if r.get("broker_check_candidate")],"broker_verify_now_count":len(urgent),"broker_verify_now_symbols":urgent,"degiro_check_count":len(fresh),"degiro_check_symbols":fresh,"delayed_provider_verify_now_symbols":delayed,"data_blocked_count":len(data_blocked),"data_blocked_symbols":data_blocked,"structure_present_but_fresh_quote_missing_count":len(structure_unverified),"structure_present_but_fresh_quote_missing_symbols":structure_unverified,"no_setup_claim_safe":len(data_blocked)==0,"trade_ready_count":0,"candidates":rows}
    (ROOT/"europe_combined_recovery_report.json").write_text(json.dumps(result,indent=2,ensure_ascii=False))
    for row in rows:print(json.dumps({k:row.get(k) for k in ("symbol","intraday_evidence","provider_freshness_class","prealert_status","broker_verify_now","trade_ready")},ensure_ascii=False),flush=True)
    print(json.dumps({k:v for k,v in result.items() if k!="candidates"},indent=2))
if __name__=="__main__":main()

