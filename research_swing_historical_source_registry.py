"""Conservative offline source registry for historical event research.

This is a review queue, NOT an authorization to scrape or redistribute data.
Check official terms and technical access before enabling any provider.
"""
SOURCES = {
    "sec_edgar": {
        "region": "US", "role": "filings_and_fundamentals",
        "official_url": "https://www.sec.gov/edgar/sec-api-documentation",
        "access": "public_documented_api",
        "historical_event_timestamps": "filing_acceptance_requires_validation",
        "license_review": "required_before_bulk_reuse",
        "automatic_ingestion_enabled": False,
    },
    "euronext_market_data": {
        "region": "EU", "role": "historical_prices",
        "official_url": "https://www.euronext.com/en/data/how-access-market-data/web-services",
        "access": "commercial_terms_to_verify",
        "historical_event_timestamps": "not_an_event_feed",
        "license_review": "required",
        "automatic_ingestion_enabled": False,
    },
    "stooq": {
        "region": "multi_market", "role": "historical_prices",
        "official_url": "https://stooq.com/",
        "access": "rate_limits_and_automation_restrictions_to_verify",
        "historical_event_timestamps": "not_an_event_feed",
        "license_review": "personal_use_and_redistribution_restrictions",
        "automatic_ingestion_enabled": False,
    },
}


def source_review_status():
    """Return a safe immutable-style snapshot, not a claim of live availability."""
    return {name: dict(info) for name, info in SOURCES.items()}


def eligible_automatic_sources():
    """Fail closed until a separate documented source approval exists."""
    return tuple(name for name, info in SOURCES.items()
                 if info["automatic_ingestion_enabled"]
                 and info["license_review"] == "approved")
