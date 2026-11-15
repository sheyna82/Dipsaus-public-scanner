"""Offline ntfy payload contract: no HTTP, topics, credentials or publishing.

Research previews cannot be promoted to trade alerts by caller-supplied flags.
This is a local serialization test seam, NOT an end-to-end delivery proof.
"""
from decimal import Decimal, InvalidOperation
from research.spoor2_notification_policy_20261111 import (
    classify_notification, notification_subject, offline_notification_route,
)


def _amount(value):
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    return format(number, ".2f") if number.is_finite() else None


def build_offline_ntfy_preview(symbol, phase, *, entry_low=None, entry_high=None,
                               invalidation=None, target=None, rr=None,
                               net_profit_eur=None, buy_fee_eur=None,
                               sell_fee_eur=None):
    """Render untrusted research values with explicit non-trade labels."""
    classification = classify_notification({"phase": phase})
    route = offline_notification_route(classification)
    base = {"status": "OFFLINE_PREVIEW_ONLY", "send_enabled": False,
            "topic_configured": False, "trade_ready": False,
            "order_placement_enabled": False, "route": route["route"]}
    if classification["channel"] != "RESEARCH" or not isinstance(symbol, str) or not symbol.strip():
        return {**base, "title": "DIPSAUS | GEEN MELDING", "body": None}
    fields = (entry_low, entry_high, invalidation, target, rr,
              net_profit_eur, buy_fee_eur, sell_fee_eur)
    values = [_amount(v) for v in fields]
    if any(v is None for v in values):
        return {**base, "title": notification_subject(symbol, classification),
                "body": None, "reason": "INCOMPLETE_FINANCIAL_PREVIEW"}
    low, high, invalid, target_p, ratio, net, buy_fee, sell_fee = map(Decimal, values)
    if not (0 < invalid < low <= high < target_p and ratio >= 2 and net >= 150
            and buy_fee >= 0 and sell_fee >= 0):
        return {**base, "title": notification_subject(symbol, classification),
                "body": None, "reason": "INVALID_RESEARCH_SCENARIO"}
    # Recompute the conservative R/R at the upper entry bound; never trust a
    # caller-provided ratio that could make an unsafe setup appear qualified.
    calculated_rr = (target_p - high) / (high - invalid)
    if calculated_rr < 2 or abs(calculated_rr - ratio) > Decimal("0.005"):
        return {**base, "title": notification_subject(symbol, classification),
                "body": None, "reason": "RR_NOT_CONSISTENT_WITH_ENTRY_ZONE"}
    lines = [
        "TEST / ONDERZOEK - GEEN KOOP OF INSTAPSIGNAAL",
        "Instrument: " + symbol.strip(),
        "Instapzone (hypothese): " + values[0] + " - " + values[1],
        "Invalidatie (hypothese): " + values[2],
        "Koersdoel (hypothese): " + values[3],
        "R/R (aangeleverd, niet onafhankelijk geverifieerd): " + values[4],
        "Nettowinst (aangeleverd, niet onafhankelijk geverifieerd): EUR " + values[5],
        "Kostenhypothese aankoop/verkoop: EUR " + values[6] + " / " + values[7],
        "Kanaal: RESEARCH_ONLY; geen trade-topic, geen order",
        "OFFLINE PREVIEW - NIET VERZONDEN",
    ]
    return {**base, "title": notification_subject(symbol, classification),
            "body": "\n".join(lines), "reason": "RESEARCH_PREVIEW_NOT_ATTESTED"}
