"""Optional Finnhub issuer profile research. Profile is not a quality verdict."""
import os
from us_news_fallback import _fetch

def company_profile(symbol, token=None):
    token = token or os.environ.get("FINNHUB_API_KEY")
    result = {"source":"Finnhub stock/profile2", "status":"UNVERIFIED",
              "issuer_name":None,"profile_symbol":None,"exchange":None,"industry":None,"country":None,
              "market_cap_million_usd_reported":None,"website":None,
              "issuer_identity_verified":False,"financial_quality_verified":False,
              "sector_verified":False,"portfolio_fit_verified":False,
              "reason":None}
    if not token:
        result.update(status="NO_API_KEY",reason="FINNHUB_API_KEY missing")
        return result
    try:
        data = _fetch("stock/profile2",{"symbol":symbol},token)
        if not isinstance(data,dict) or not data.get("name") or not data.get("ticker"):
            result.update(status="EMPTY_OR_INVALID_PROFILE",reason="No issuer profile returned")
            return result
        if str(data["ticker"]).upper() != symbol.upper():
            result.update(status="TICKER_MISMATCH",reason="Returned ticker differs from requested symbol")
            return result
        result.update(status="PROFILE_RESEARCH_AVAILABLE",
                      issuer_name=data.get("name"),profile_symbol=data.get("ticker"),exchange=data.get("exchange"),
                      industry=data.get("finnhubIndustry"),country=data.get("country"),
                      market_cap_million_usd_reported=data.get("marketCapitalization"),
                      website=data.get("weburl"),
                      reason="Provider profile only; independently verify issuer, financials, corporate actions and portfolio overlap")
    except Exception as exc:
        result.update(status="FETCH_FAILED",reason=type(exc).__name__)
    return result

