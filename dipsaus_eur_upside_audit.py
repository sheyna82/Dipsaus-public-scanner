"""Private, read-only diagnostics for missing EUR upside evidence.

Do not turn monitoring pivots into verified resistance or invalidation.
"""
from dipsaus_eur_upside import estimate_gross_eur

REQUIRED = (
    "provider_quote", "provider_quote_utc", "provider_freshness_pass",
    "resistance_usd", "resistance_checked_utc", "resistance_verified",
    "invalidation_usd", "invalidation_checked_utc", "invalidation_verified",
    "eur_per_usd", "fx_checked_utc",
)


def audit_row(row, now=None):
    result = estimate_gross_eur(row, now=now)
    missing = [key for key in REQUIRED if key not in row or row[key] is None]
    unverified = [key for key in ("provider_freshness_pass", "resistance_verified",
                                  "invalidation_verified") if row.get(key) is not True]
    return {"symbol": row.get("symbol"), "status": result["status"],
            "missing_fields": missing, "unverified_fields": unverified,
            "trade_ready": False}


def audit_rows(rows, now=None):
    records = [audit_row(row, now=now) for row in rows if isinstance(row, dict)
               and row.get("market") == "US"]
    return {"total_us_rows": len(records),
            "research_estimates": sum(x["status"] == "RESEARCH_ESTIMATE" for x in records),
            "unavailable": sum(x["status"] != "RESEARCH_ESTIMATE" for x in records),
            "rows": records, "mode": "PRIVATE_RESEARCH_DIAGNOSTICS_ONLY"}
