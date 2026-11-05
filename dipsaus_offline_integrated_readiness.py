"""Conservative integration of offline data readiness audits.

A structurally valid source is not enough for a predictive backtest.
This gate requires independently verified external provenance and an untouched
holdout. It never certifies predictive skill or enables live trading.
"""


def audit_integrated_readiness(*, source_rows, earnings_asof, earnings_coverage,
                               security_master, independent_corporate_actions=False,
                               independent_delisted_inventory=False,
                               frozen_holdout=False):
    if not isinstance(source_rows, (list, tuple)) or not source_rows:
        return {"status": "DATA_BLOCKED", "reason": "no_price_sources", "trade_ready": False}
    for row in source_rows:
        if not isinstance(row, dict) or row.get("status") != "OHLCV_VALIDATED":
            return {"status": "DATA_BLOCKED", "reason": "price_source_rejected",
                    "trade_ready": False}
    if not isinstance(earnings_asof, dict) or earnings_asof.get("status") != "ASOF_ATTESTATION_ONLY":
        return {"status": "DATA_BLOCKED", "reason": "earnings_asof_unverified",
                "trade_ready": False}
    if not isinstance(earnings_coverage, dict) or earnings_coverage.get("status") != "INVENTORY_MATCH":
        return {"status": "DATA_BLOCKED", "reason": "earnings_inventory_unverified",
                "trade_ready": False}
    if not isinstance(security_master, dict) or security_master.get("status") != "IDENTITY_REVIEW_REQUIRED":
        return {"status": "DATA_BLOCKED", "reason": "security_identity_unverified",
                "trade_ready": False}
    if not all((independent_corporate_actions, independent_delisted_inventory, frozen_holdout)):
        return {"status": "DATA_BLOCKED", "reason": "external_evidence_missing",
                "trade_ready": False}
    # An issuer-level inventory match does not prove every earnings event was
    # captured, nor does an asserted boolean prove the external evidence.
    return {"status": "MANUAL_INDEPENDENT_AUDIT_REQUIRED",
            "reason": "event_completeness_and_provenance_not_independently_established",
            "predictive_edge_verified": False, "trade_ready": False}
