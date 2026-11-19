"""Explicit, isolated ntfy transport probe. No production topic or trade signals."""
import os
import re
import urllib.request
from research.spoor2_eu_money_scenario_20261111 import european_money_scenario
from research.spoor2_ntfy_preview_contract_20261115 import build_offline_ntfy_preview

SERVER = "https://ntfy.sh"
TEST_TITLE = "DIPSAUS | TEST - GEEN HANDELSSIGNAAL"
TEST_BODY = ("TEST - GEEN HANDELSSIGNAAL\n"
             "Spoor 2 onderzoeksomgeving: ntfy afleverproef.\n"
             "Geen echte koers, geen order, geen instapadvies.")


def financial_test_message():
    """Compute synthetic EUR scenario; never represent it as trade-ready."""
    scenario = european_money_scenario(
        quote_unit="EUR", ask="50", target_bid="55", invalidation="47.50",
        budget_eur="3500", eur_per_base_unit="1", buy_fee_eur="4.90",
        sell_fee_eur="4.90", buy_fx_rate="0", sell_fx_rate="0",
    )
    if scenario["status"] != "ILLUSTRATIVE_NOT_VERIFIED" or scenario["trade_ready"]:
        raise ValueError("UNSAFE_FINANCIAL_SCENARIO")
    preview = build_offline_ntfy_preview(
        "DEMO-EUR", "BREAKOUT-SEEN", entry_low="49.50", entry_high="50",
        invalidation="47.50", target="55",
        rr=scenario["reference_rr"], net_profit_eur=scenario["net_profit_eur"],
        buy_fee_eur="4.90", sell_fee_eur="4.90",
    )
    if preview["route"] != "RESEARCH_ONLY" or preview["body"] is None:
        raise ValueError("RESEARCH_PREVIEW_REJECTED")
    if preview["send_enabled"] or preview["trade_ready"]:
        raise ValueError("UNSAFE_PREVIEW_FLAGS")
    return ("DIPSAUS | TEST BEREKEND - GEEN HANDELSSIGNAAL",
            preview["body"].replace("OFFLINE PREVIEW - NIET VERZONDEN",
                                    "FICTIEVE CI-TEST - GEEN HANDELSSIGNAAL")
            + "\\nAantal hele aandelen: " + str(scenario["whole_shares"])
            + "\\nTotale aankoop (EUR): " + scenario["purchase_eur"])


def prepare_probe(topic, *, enabled=False, financial=False):
    if enabled is not True:
        raise ValueError("EXPLICIT_TEST_OPT_IN_REQUIRED")
    if not isinstance(topic, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,100}", topic):
        raise ValueError("INVALID_PRIVATE_TEST_TOPIC")
    if topic.lower().startswith(("dipsaus", "trade", "signal", "prod", "live")):
        raise ValueError("POSSIBLE_PRODUCTION_TOPIC")
    title, body = financial_test_message() if financial is True else (TEST_TITLE, TEST_BODY)
    return urllib.request.Request(
        SERVER + "/" + topic, data=body.encode("utf-8"),
        headers={"Title": title, "Priority": "default",
                 "Tags": "test_tube", "Content-Type": "text/plain; charset=utf-8"},
        method="POST",
    )


def main():
    topic = os.environ.get("DIPSAUS_NTFY_TEST_TOPIC", "")
    enabled = os.environ.get("DIPSAUS_NTFY_TEST_SEND") == "YES_I_APPROVE_TEST"
    financial = os.environ.get("DIPSAUS_NTFY_FINANCIAL_TEST") == "YES_SYNTHETIC_FINANCIAL_TEST"
    request = prepare_probe(topic, enabled=enabled, financial=financial)
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("NTFY_NON_200_RESPONSE")
    print("TEST_PUBLISH_ACCEPTED_BY_NTFY_NOT_PHONE_DELIVERY_PROOF")


if __name__ == "__main__":
    main()
