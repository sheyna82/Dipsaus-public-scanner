"""Offline research readiness report: machine-readable blockers, not trading signals.

Inputs are outputs of separate source checks. A failed/absent prerequisite is
always listed, and even a fully asserted set requires independent manual audit.
"""


def readiness_report(*, source_rows, earnings_asof, earnings_coverage,
                     security_master, corporate_actions_verified=False,
                     delisted_inventory_verified=False, holdout_frozen=False):
    checks = {
        "price_history": isinstance(source_rows, (list, tuple)) and bool(source_rows)
                         and all(isinstance(row, dict) and row.get("status") == "OHLCV_VALIDATED"
                                 for row in source_rows),
        "earnings_publication_asof": isinstance(earnings_asof, dict)
                                    and earnings_asof.get("status") == "ASOF_ATTESTATION_ONLY",
        "earnings_issuer_inventory": isinstance(earnings_coverage, dict)
                                     and earnings_coverage.get("status") == "INVENTORY_MATCH",
        "historical_security_identity": isinstance(security_master, dict)
                                         and security_master.get("status") == "IDENTITY_REVIEW_REQUIRED",
        "corporate_actions_independently_verified": corporate_actions_verified is True,
        "delisted_inventory_independently_verified": delisted_inventory_verified is True,
        "holdout_preregistered": holdout_frozen is True,
    }
    blocked = [name for name, passed in checks.items() if not passed]
    return {
        "status": "DATA_BLOCKED" if blocked else "MANUAL_INDEPENDENT_AUDIT_REQUIRED",
        "passed_checks": [name for name, passed in checks.items() if passed],
        "blocked_checks": blocked,
        "independent_event_completeness_verified": False,
        "predictive_edge_verified": False,
        "trade_ready": False,
    }
