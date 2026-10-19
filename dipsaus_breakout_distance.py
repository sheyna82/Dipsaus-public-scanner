"""Research-only distance-to-breakout context for US phase notifications.

This is not an entry gate: missing price/level is UNKNOWN, not a green light.
"""
import math


def breakout_distance(row):
    if row.get("market") != "US":
        return {"status": "NOT_APPLICABLE"}
    price = row.get("provider_quote")
    level = row.get("route_2_break_above")
    if (not isinstance(price, (int, float)) or isinstance(price, bool)
            or not isinstance(level, (int, float)) or isinstance(level, bool)
            or not math.isfinite(price) or not math.isfinite(level)
            or price <= 0 or level <= 0):
        return {"status": "UNKNOWN"}
    distance = 100 * (price / level - 1)
    return {"status": "EXTENDED" if distance >= 3 else "BELOW_BREAKOUT" if distance < 0 else "NEAR_BREAKOUT",
            "distance_pct": round(distance, 2)}


def message_context(row):
    result = breakout_distance(row)
    if result["status"] == "EXTENDED":
        return ("\nLATE-BREAKOUT WATCH: providerkoers staat "
                + str(result["distance_pct"])
                + "% boven het aangeleverde uitbraakniveau. "
                "Niet achtervolgen; controleer nieuwe instapstructuur, actuele weerstand, "
                "R/R >=2 en realistische bruto EUR-winst. GEEN koopbevestiging.")
    if result["status"] == "UNKNOWN":
        return ("\nRESTERENDE WINSTRUIMTE ONBEKEND: uitbraakniveau of verse "
                "prijsvergelijking ontbreekt. Geen instapbevestiging.")
    return ("\nUitbraakafstand: " + str(result["distance_pct"])
            + "%. Nog geen bevestiging van resterende EUR-winst of R/R.")
