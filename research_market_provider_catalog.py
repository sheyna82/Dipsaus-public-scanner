"""Research-only market-data provider catalog.

Catalog entries are candidates, not authenticated or successfully tested APIs.
Never put credentials in this repository. Do not enable network requests here.
"""

PROVIDERS = {
    "tiingo": {"role": "historical_primary_candidate", "auth": "api_token",
               "endpoint": "https://api.tiingo.com/tiingo/daily/{symbol}/prices",
               "adjustments": "raw_and_adjusted", "verification": "pending"},
    "twelve_data": {"role": "historical_crosscheck_candidate", "auth": "api_key",
                    "endpoint": "https://api.twelvedata.com/time_series",
                    "adjustments": "verify_per_endpoint", "verification": "pending"},
    "alpha_vantage": {"role": "historical_crosscheck_candidate", "auth": "api_key",
                      "endpoint": "https://www.alphavantage.co/query",
                      "adjustments": "verify_free_tier", "verification": "pending"},
    "finnhub": {"role": "earnings_and_market_candidate", "auth": "api_key",
                "endpoint": "https://finnhub.io/api/v1",
                "adjustments": "verify_per_endpoint", "verification": "pending"},
    "massive": {"role": "us_market_candidate", "auth": "api_key",
                "endpoint": "https://api.massive.com",
                "adjustments": "verify_free_tier", "verification": "pending"},
    "alpaca": {"role": "us_market_candidate", "auth": "api_credentials",
               "endpoint": "https://data.alpaca.markets",
               "adjustments": "verify_per_feed", "verification": "pending"},
    "stooq": {"role": "historical_fallback_candidate", "auth": "unknown",
              "endpoint": "https://stooq.com/q/d/l/",
              "adjustments": "unknown", "verification": "pending"},
    "financial_modeling_prep": {"role": "fundamentals_candidate", "auth": "api_key",
                                "endpoint": "https://financialmodelingprep.com/stable",
                                "adjustments": "verify_per_endpoint", "verification": "pending"},
    "nasdaq_data_link": {"role": "dataset_candidate", "auth": "api_key",
                         "endpoint": "https://data.nasdaq.com/api/v3",
                         "adjustments": "dataset_specific", "verification": "pending"},
    "yfinance": {"role": "experimental_crosscheck_only", "auth": "unofficial",
                 "endpoint": "https://finance.yahoo.com",
                 "adjustments": "library_dependent", "verification": "pending"},
}

REQUIRED_CHECKS = (
    "historical_coverage", "free_tier_entitlement", "terms_internal_use",
    "adjusted_vs_raw", "timezone_and_calendar", "corporate_actions",
    "rate_limits", "authentication_and_secret_handling",
    "independent_price_crosscheck",
)


def candidate_report():
    return {
        "provider_count": len(PROVIDERS),
        "providers": PROVIDERS,
        "required_checks": list(REQUIRED_CHECKS),
        "provider_integrations_enabled": False,
        "live_scanner_modified": False,
        "verified_market_data_available": False,
        "trade_ready": False,
    }
