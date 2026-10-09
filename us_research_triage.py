"""Research queue triage only. Do not infer executable liquidity from daily volume."""
def liquidity_triage(candidate):
    price = candidate.get("last_close_usd")
    volume = candidate.get("last_volume_shares")
    avg = candidate.get("average_20d_volume_shares")
    turnover = round(price * avg, 2) if isinstance(price,(int,float)) and isinstance(avg,(int,float)) else None
    reasons = []
    if not isinstance(price,(int,float)) or price <= 0:
        reasons.append("PRICE_UNKNOWN")
    elif price < 1:
        reasons.append("SUB_DOLLAR_PRICE")
    elif price < 5:
        reasons.append("LOW_PRICE_UNDER_5_USD")
    if turnover is None:
        reasons.append("HISTORICAL_TURNOVER_UNKNOWN")
    elif turnover < 1_000_000:
        reasons.append("LOW_HISTORICAL_DOLLAR_TURNOVER")
    return {"historical_20d_avg_volume_shares":avg,
            "historical_20d_avg_dollar_turnover_usd":turnover,
            "last_daily_volume_shares":volume,
            "flags":reasons,"broker_spread_verified":False,
            "broker_depth_verified":False,"status":"MANUAL_LIQUIDITY_REVIEW" if reasons else "BROKER_LIQUIDITY_UNVERIFIED"}

def research_queue(candidates, limit=3):
    """Keep all candidates; exclude liquidity-flagged names only from priority queue."""
    for c in candidates:
        c["liquidity_triage"] = liquidity_triage(c)
    eligible = [c for c in candidates
                if c["research_triage"]["space_to_first_overhead_pct"] is not None
                and c["research_triage"]["space_to_first_overhead_pct"] > 1
                and not c["liquidity_triage"]["flags"]]
    eligible.sort(key=lambda x:(
        -(x["recovery_map"]["weekly_structure"]["completed_week_close_rising"] is True),
        -(x["recovery_map"]["weekly_structure"]["completed_week_higher_low"] is True),
        -x["recovery_map"]["bottom_signal_count"],
        -x["research_triage"]["space_to_first_overhead_pct"],x["symbol"]))
    return eligible[:limit], {
        "near_overhead":[c["symbol"] for c in candidates if c["research_triage"]["space_to_first_overhead_pct"] is None or c["research_triage"]["space_to_first_overhead_pct"] <= 1],
        "liquidity_review":[c["symbol"] for c in candidates if c["liquidity_triage"]["flags"]]}

