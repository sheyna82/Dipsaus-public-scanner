"""Explicit, isolated ntfy transport probe. No production topic or trade signals."""
import os
import re
import urllib.request

SERVER = "https://ntfy.sh"
TEST_TITLE = "DIPSAUS | TEST - GEEN HANDELSSIGNAAL"
TEST_BODY = ("TEST - GEEN HANDELSSIGNAAL\n"
             "Spoor 2 onderzoeksomgeving: ntfy afleverproef.\n"
             "Geen echte koers, geen order, geen instapadvies.")


def prepare_probe(topic, *, enabled=False):
    if enabled is not True:
        raise ValueError("EXPLICIT_TEST_OPT_IN_REQUIRED")
    if not isinstance(topic, str) or not re.fullmatch(r"[A-Za-z0-9_-]{16,100}", topic):
        raise ValueError("INVALID_PRIVATE_TEST_TOPIC")
    if topic.lower().startswith(("dipsaus", "trade", "signal", "prod", "live")):
        raise ValueError("POSSIBLE_PRODUCTION_TOPIC")
    return urllib.request.Request(
        SERVER + "/" + topic, data=TEST_BODY.encode("utf-8"),
        headers={"Title": TEST_TITLE, "Priority": "default",
                 "Tags": "test_tube", "Content-Type": "text/plain; charset=utf-8"},
        method="POST",
    )


def main():
    topic = os.environ.get("DIPSAUS_NTFY_TEST_TOPIC", "")
    enabled = os.environ.get("DIPSAUS_NTFY_TEST_SEND") == "YES_I_APPROVE_TEST"
    request = prepare_probe(topic, enabled=enabled)
    with urllib.request.urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError("NTFY_NON_200_RESPONSE")
    print("TEST_PUBLISH_ACCEPTED_BY_NTFY_NOT_PHONE_DELIVERY_PROOF")


if __name__ == "__main__":
    main()
