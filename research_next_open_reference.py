"""Research-only post-registration opening-price eligibility; never an order."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo


def assess_next_open_reference(*, registered_at_utc, stock_bar, benchmark_bar):
    registered = datetime.fromisoformat(registered_at_utc)
    if registered.tzinfo is None or registered.utcoffset() is None:
        raise ValueError("registration_timezone_required")
    registration_day = registered.astimezone(ZoneInfo("America/New_York")).date().isoformat()
    def check(bar, expected):
        if not isinstance(bar, dict) or bar.get("symbol") != expected:
            raise ValueError("entry_symbol_mismatch")
        if bar.get("session") <= registration_day:
            raise ValueError("entry_not_after_registration_day")
        observed = datetime.fromisoformat(bar["retrieved_at_utc"])
        if observed.tzinfo is None or observed.utcoffset() is None:
            raise ValueError("entry_receipt_timezone_required")
        if observed < registered:
            raise ValueError("entry_data_observed_before_registration")
        try:
            price = Decimal(str(bar["open"]))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("invalid_entry_open") from exc
        if not price.is_finite() or price <= 0:
            raise ValueError("invalid_entry_open")
        return price
    if not isinstance(stock_bar, dict) or not isinstance(benchmark_bar, dict):
        raise ValueError("invalid_entry_bars")
    if not isinstance(stock_bar.get("symbol"), str) or not stock_bar["symbol"]:
        raise ValueError("invalid_stock_symbol")
    if not isinstance(stock_bar.get("session"), str) or not isinstance(benchmark_bar.get("session"), str):
        raise ValueError("invalid_entry_session")
    if stock_bar.get("session") != benchmark_bar.get("session"):
        raise ValueError("entry_sessions_not_aligned")
    stock = check(stock_bar, stock_bar.get("symbol"))
    spy = check(benchmark_bar, "SPY")
    if stock_bar.get("symbol") == "SPY":
        raise ValueError("stock_must_differ_from_benchmark")
    # Caller-controlled verification flags are not proof of vendor authenticity.
    # Keep price observations as provisional research references only.
    return {"status": "provisional_unverified_entry_reference",
            "research_only": True, "trade_ready": False,
            "entry_reference_accepted": False,
            "entry_session": stock_bar["session"], "stock_open": str(stock),
            "benchmark_open": str(spy), "execution_price_verified": False,
            "source_authenticated_independently": False}
