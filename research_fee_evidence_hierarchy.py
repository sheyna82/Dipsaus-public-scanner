"""Research-only fee evidence hierarchy; never authenticates account or orders.

Public schedules can support illustrative assumptions, not executable costs.
An order-preview claim is still untrusted until independently authenticated.
"""
BLOCKED = {"trade_ready": False, "order_placement_enabled": False,
           "degiro_fee_verified": False,
           "source_authenticity_independently_verified": False}

def classify_fee_evidence(evidence):
    base = {**BLOCKED, "status": "FEE_EVIDENCE_BLOCKED"}
    if not isinstance(evidence, dict):
        return {**base, "reason": "INVALID_INPUT"}
    kind = evidence.get("evidence_kind")
    if kind == "OFFICIAL_PUBLIC_SCHEDULE":
        if evidence.get("account_specific") is True:
            return {**base, "reason": "PUBLIC_SCHEDULE_CANNOT_ATTEST_ACCOUNT"}
        return {**BLOCKED, "status": "PUBLIC_FEE_ASSUMPTION_ONLY",
                "note": "Public fee schedule is not an authenticated order cost."}
    if kind == "BROKER_ORDER_PREVIEW":
        # A buy-order preview cannot establish future sell execution fees.
        if evidence.get("sell_fee_basis") != "UNVERIFIED_FUTURE_SELL_ESTIMATE":
            return {**base, "reason": "FUTURE_SELL_FEE_BASIS_NOT_DECLARED"}
        if (evidence.get("preview_isin") != evidence.get("isin")
                or evidence.get("preview_operating_mic") != evidence.get("operating_mic")
                or type(evidence.get("preview_quantity")) is not int
                or evidence["preview_quantity"] <= 0):
            return {**base, "reason": "PREVIEW_IDENTITY_OR_QUANTITY_MISMATCH"}
        return {**BLOCKED, "status": "UNAUTHENTICATED_ORDER_PREVIEW_CLAIM",
                "note": "A caller-supplied preview claim cannot establish actual broker costs."}
    return {**base, "reason": "UNKNOWN_FEE_EVIDENCE_KIND"}
