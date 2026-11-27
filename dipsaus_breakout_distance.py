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
                "R/R >=2 en verwachte netto EUR-winst. GEEN koopbevestiging.")
    if result["status"] == "UNKNOWN":
        return ("\nRESTERENDE WINSTRUIMTE ONBEKEND: uitbraakniveau of verse "
                "prijsvergelijking ontbreekt. Geen instapbevestiging.")
    return ("\nUitbraakafstand: " + str(result["distance_pct"])
            + "%. Nog geen bevestiging van resterende EUR-winst of R/R.")


def historical_resistance_context(row):
    room = row.get("resistance_room") or {}
    status = room.get("status")
    if status in ("PASSED", "REACHED"):
        state = "gepasseerd" if status == "PASSED" else "bereikt"
        return (f"\nEerste historische weerstand {room['level']:.4f} is {state}. "
                "Actuele winstruimte vereist een geverifieerde eerste weerstand.")
    if status == "AHEAD":
        return (f"\nAfstand tot eerste historische referentie vanaf de providerkoers "
                f"{room['remaining_pct']:.2f}%. Actuele weerstand en uitvoerbaarheid moeten worden gecontroleerd.")
    return "\nActuele winstruimte onbekend."
