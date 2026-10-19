"""Conservative gross EUR upside estimate, research-only.

Requires independently verified and fresh quote, resistance, invalidation and FX.
No invented targets, no broker-executable pricing, no buy/sell signals.
"""
import math
from datetime import datetime, timezone

MAX_AGE_SECONDS = 900


def _valid_stamp(value, now):
    if not isinstance(value, str):
        return False
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.tzinfo is not None and -30 <= (now - dt).total_seconds() <= MAX_AGE_SECONDS
    except (ValueError, TypeError, OverflowError):
        return False


def _positive(value):
    return (isinstance(value, (float, int)) and not isinstance(value, bool)
            and math.isfinite(value) and value > 0)


def estimate_gross_eur(row, tranche_eur=3500, now=None):
    """Return incomplete unless all independently sourced money inputs are supplied.

    resistance_usd: first meaningful *verified* resistance; not a chart screenshot.
    invalidation_usd: structural invalidation from independent setup.
    eur_per_usd: observed EUR value of one USD, timestamped separately.
    """
    now = now or datetime.now(timezone.utc)
    unknown = {"status": "UNKNOWN", "trade_ready": False,
               "reason": "MISSING_OR_STALE_VERIFIED_MONEY_INPUTS"}
    if not isinstance(row, dict) or row.get("market") != "US":
        return unknown
    keys = ("provider_quote", "resistance_usd", "invalidation_usd", "eur_per_usd")
    if not all(_positive(row.get(k)) for k in keys) or not _positive(tranche_eur):
        return unknown
    if row.get("provider_freshness_pass") is not True:
        return unknown
    if not all(_valid_stamp(row.get(k), now) for k in
               ("provider_quote_utc", "resistance_checked_utc",
                "invalidation_checked_utc", "fx_checked_utc")):
        return unknown
    if row.get("resistance_verified") is not True or row.get("invalidation_verified") is not True:
        return unknown
    price, target, stop, fx = (row[k] for k in keys)
    if not stop < price < target:
        return {"status": "UNFAVORABLE_STRUCTURE", "trade_ready": False,
                "reason": "TARGET_NOT_ABOVE_ENTRY_OR_INVALIDATION_NOT_BELOW"}
    shares = math.floor(tranche_eur / (price * fx))
    if shares <= 0:
        return unknown
    gross = shares * (target - price) * fx
    risk = shares * (price - stop) * fx
    return {"status": "RESEARCH_ESTIMATE", "trade_ready": False,
            "shares_estimate": shares, "gross_eur": round(gross, 2),
            "risk_eur": round(risk, 2), "rr": round(gross / risk, 2),
            "fees_spread_slippage_excluded": True,
            "reason": "NOT_BROKER_VERIFIED_OR_EXECUTABLE"}


def message_context(row, now=None):
    result = estimate_gross_eur(row, now=now)
    if result["status"] != "RESEARCH_ESTIMATE":
        return ("\nBruto EUR-winstruimte: NIET BEREKENBAAR zonder verse, "
                "onafhankelijk bevestigde weerstand, invalidatie en EUR/USD. "
                "Geen koopbevestiging.")
    return ("\nONDERZOEKSSCHATTING (geen koopbevestiging): "
            "bruto potentieel EUR " + str(result["gross_eur"])
            + ", structureel risico EUR " + str(result["risk_eur"])
            + ", R/R " + str(result["rr"])
            + " bij indicatieve tranche EUR 3500. "
            "Bied/laat, spread, kosten, slippage en actuele weerstand "
            "nog via DEGIRO controleren.")
