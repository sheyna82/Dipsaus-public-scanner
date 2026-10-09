"""Research dossiers: separate historical setup from company/event and broker checks."""
def dossier(candidate, queue_item):
    triage = candidate["research_triage"]
    liquidity = candidate["liquidity_triage"]
    event = queue_item["event_research"]
    alt = queue_item["alternative_event_research"]
    headlines = alt.get("headline_review", [])
    flagged = alt.get("flagged_headline_review", [h for h in headlines if h.get("keyword_flag")])
    weekly = candidate["recovery_map"]["weekly_structure"]
    return {
        "symbol":candidate["symbol"], "name":candidate["name"],
        "historical_bar_date":candidate["last_bar_date"],
        "historical_close_usd":candidate["last_close_usd"],
        "bottom_signals":candidate["recovery_map"]["bottom_signal_count"],
        "weekly_completed_close_rising":weekly["completed_week_close_rising"],
        "weekly_completed_higher_low":weekly["completed_week_higher_low"],
        "first_overhead_reference_usd":triage["first_overhead_reference_usd"],
        "historical_space_to_first_overhead_pct":triage["space_to_first_overhead_pct"],
        "historical_invalidation_reference_usd":candidate["recovery_map"].get("recent_10d_low_invalidation_reference_usd"),
        "historical_pivot_zones":candidate["recovery_map"]["historical_overhead_pivot_zones"][:5],
        "liquidity":liquidity,
        "company_event": {
            "sec_status":event["status"],
            "filing_content_reviews":event.get("filing_content_reviews",[]),
            "news_status":alt.get("news_status","NOT_CHECKED"),
            "earnings_status":alt.get("earnings_status","NOT_CHECKED"),
            "flagged_headlines":flagged[:10],
            "all_recent_headlines_count":alt.get("headline_count_total",len(headlines)),
            "flagged_headlines_total":alt.get("flagged_count_total",len(flagged)),
            "news_review_incomplete":alt.get("news_status") != "FETCHED",
            "earnings_dates":alt.get("earnings_dates",[]),
            "event_risk_cleared":False,
            "corporate_actions_cleared":False,
        },
        "portfolio_fit": {
            "status":"NOT_VERIFIED",
            "sector":"NOT_VERIFIED",
            "shared_drivers":"NOT_VERIFIED",
            "existing_position_overlap":"NOT_VERIFIED",
        },
        "manual_review_questions":[
            "Verify issuer, listing, sector, profitability/balance-sheet and current material news",
            "Read flagged headlines and primary filings; verify next earnings date and corporate actions",
            "Check portfolio overlap, shared macro drivers and correlation",
            "Validate daily/weekly bottom, first meaningful resistance and farther recovery zone",
            "Get timestamped DEGIRO bid/ask, spread, depth and current EUR/USD",
            "Run EUR 3500 money/risk gate with structural invalidation and R/R >= 2",
        ],
        "status":"RESEARCH_DOSSIER_ONLY_NO_BUY_SIGNAL",
        "trade_ready":False,
    }

