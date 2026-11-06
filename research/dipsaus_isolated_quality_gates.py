"""Isolated cost and signal provenance gates. Never connect to a broker."""
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation

def amount(value, positive=False):
    if isinstance(value, bool):
        raise ValueError("INVALID_AMOUNT")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("INVALID_AMOUNT") from exc
    if not d.is_finite() or (d <= 0 if positive else d < 0):
        raise ValueError("INVALID_AMOUNT")
    return d

def net_round_trip(*, shares, buy_ask, sell_bid, buy_eur_per_quote,
                   sell_eur_per_quote, buy_broker_fee_eur,
                   sell_broker_fee_eur, buy_fx_fee_eur, sell_fx_fee_eur,
                   buy_slippage_per_share="0", sell_slippage_per_share="0",
                   fee_basis="explicit_eur", fx_basis="eur_per_quote"):
    """Bid/ask includes spread; FX must exclude any separately charged FX fee."""
    if fee_basis != "explicit_eur" or fx_basis != "eur_per_quote":
        raise ValueError("AMBIGUOUS_FEE_OR_FX_BASIS")
    qty = amount(shares, True)
    if qty != qty.to_integral_value():
        raise ValueError("WHOLE_SHARES_REQUIRED")
    ask, bid = amount(buy_ask, True), amount(sell_bid, True)
    buyfx, sellfx = amount(buy_eur_per_quote, True), amount(sell_eur_per_quote, True)
    bslip, sslip = amount(buy_slippage_per_share), amount(sell_slippage_per_share)
    if bid <= sslip:
        raise ValueError("INVALID_SELL_EXECUTION")
    buyfee, sellfee, buyfxfee, sellfxfee = [amount(x) for x in
        (buy_broker_fee_eur, sell_broker_fee_eur, buy_fx_fee_eur, sell_fx_fee_eur)]
    entry = qty * (ask + bslip) * buyfx + buyfee + buyfxfee
    exit_ = qty * (bid - sslip) * sellfx - sellfee - sellfxfee
    return {"research_only": True, "trade_ready": False, "orders_generated": False,
            "entry_cash_out_eur": str(entry), "exit_cash_in_eur": str(exit_),
            "net_realized_pnl_eur": str(exit_ - entry),
            "net_return_pct": str(100 * (exit_ - entry) / entry),
            "explicit_fees_eur": str(buyfee + sellfee + buyfxfee + sellfxfee),
            "spread_already_in_bid_ask": True,
            "broker_statement_reconciled": False}

def _stamp(value):
    if not isinstance(value, str):
        raise ValueError("INVALID_TIMESTAMP")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, OverflowError) as exc:
        raise ValueError("INVALID_TIMESTAMP") from exc
    if dt.tzinfo is None:
        raise ValueError("NAIVE_TIMESTAMP")
    return dt.astimezone(timezone.utc)

def verify_signal_freshness(row, *, now, max_quote_age_seconds=120,
                            max_signal_age_seconds=120, max_future_skew_seconds=5):
    """Checks chronology, NOT independently authenticated provider origin."""
    if not isinstance(row, dict) or not isinstance(now, datetime) or now.tzinfo is None:
        return {"eligible": False, "reason": "INVALID_INPUT"}
    if not all(type(x) is int and x >= 0 for x in
               (max_quote_age_seconds, max_signal_age_seconds, max_future_skew_seconds)):
        return {"eligible": False, "reason": "INVALID_POLICY"}
    if row.get("provider_freshness_pass") is not True:
        return {"eligible": False, "reason": "PROVIDER_NOT_VERIFIED"}
    if row.get("prealert_trigger_observed") is not True:
        return {"eligible": False, "reason": "TRIGGER_NOT_OBSERVED"}
    try:
        quote, signal = _stamp(row.get("provider_quote_utc")), _stamp(row.get("signal_generated_utc"))
    except (ValueError, TypeError):
        return {"eligible": False, "reason": "INVALID_OR_MISSING_TIMESTAMPS"}
    if quote > signal + timedelta(seconds=max_future_skew_seconds):
        return {"eligible": False, "reason": "SIGNAL_PRECEDES_QUOTE"}
    now_utc = now.astimezone(timezone.utc)
    if any((now_utc - dt).total_seconds() < -max_future_skew_seconds for dt in (quote, signal)):
        return {"eligible": False, "reason": "FUTURE_TIMESTAMP"}
    if (now_utc - quote).total_seconds() > max_quote_age_seconds or (now_utc - signal).total_seconds() > max_signal_age_seconds:
        return {"eligible": False, "reason": "STALE_INPUT"}
    return {"eligible": True, "reason": "CHRONOLOGY_AND_FRESHNESS_PASSED",
            "source_authenticity_independently_proven": False, "trade_ready": False}

def pivot_confirmation_dates(rows, *, span=2):
    """A historical pivot is usable only on/after its later confirmation bar."""
    if type(span) is not int or span < 1 or not isinstance(rows, list):
        raise ValueError("INVALID_PIVOT_INPUT")
    dates = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("INVALID_OHLCV")
        try:
            dt = datetime.strptime(row["date"], "%Y-%m-%d").date()
            hi, lo, op, cl = [amount(row[k]) for k in ("high", "low", "open", "close")]
            amount(row["volume"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("INVALID_OHLCV") from exc
        if hi < max(lo, op, cl) or lo > min(hi, op, cl) or lo <= 0:
            raise ValueError("INVALID_OHLCV")
        if dates and dt <= dates[-1]:
            raise ValueError("UNSORTED_OR_DUPLICATE_DATES")
        dates.append(dt)
    out = []
    for i in range(span, len(rows) - span):
        high = amount(rows[i]["high"])
        if high > max(amount(x["high"]) for x in rows[i-span:i]) and high >= max(amount(x["high"]) for x in rows[i+1:i+span+1]):
            out.append({"pivot_date": str(dates[i]), "first_available_date": str(dates[i+span]),
                        "high": str(high), "trade_ready": False})
    return out
