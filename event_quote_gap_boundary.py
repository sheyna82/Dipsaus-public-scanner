"""Isolated research-only quote diagnostic boundary; never raises to scanner."""
from datetime import datetime, timezone


def safe_quote_gap_research(rows, now=None, summarize=None):
    """Return redacted fail-closed aggregates even if research code fails."""
    try:
        if summarize is None:
            from event_quote_gap_summary import summarize_event_quote_gaps
            summarize = summarize_event_quote_gaps
        result = summarize(rows, now or datetime.now(timezone.utc),
                           expected_currency=None)
        if not isinstance(result, dict) or result.get("execution_ready") is not False:
            raise ValueError("unsafe research result")
        return result
    except Exception:
        # No exception text or private input in output.
        return {"status": "RESEARCH_ERROR", "execution_ready": False,
                "identity_independently_verified": False,
                "broker_quote_verified": False}
