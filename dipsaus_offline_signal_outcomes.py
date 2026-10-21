"""Pure offline signal-outcome study. No provider, broker, secrets or notifications.

Prices must be chronologically ordered, split-adjusted daily OHLC observations.
A signal is evaluated strictly from the NEXT trading session open; this avoids
assuming fills at a price known only after a signal was observed.
"""
import math
from datetime import date


def _price(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def evaluate_signal(prices, signal_index, horizons=(1, 3, 5, 10),
                    roundtrip_cost_bps=0, price_metadata=None):
    """Evaluate forward returns and excursion using supplied OHLC rows.

    Requires caller-attested split-adjusted, internally consistent OHLC data.\n    This metadata is NOT independent verification of the provider.\n    Returns None for invalid inputs. Incomplete horizons remain None, never
    silently converted to zero or truncated. Roundtrip cost is a simple
    explicit assumption (basis points), NOT an execution or fill simulation.
    """
    # Require explicit caller-provided provenance; never infer adjusted prices.
    if (not isinstance(price_metadata, dict)
            or price_metadata.get("split_adjusted") is not True
            or price_metadata.get("ohlc_consistent") is not True
            or not isinstance(price_metadata.get("source"), str)
            or not price_metadata["source"].strip()
            or not isinstance(price_metadata.get("currency"), str)
            or len(price_metadata["currency"]) != 3
            or not price_metadata["currency"].isalpha()
            or price_metadata["currency"] != price_metadata["currency"].upper()):
        return None
    if not isinstance(prices, (list, tuple)) or not isinstance(signal_index, int) or isinstance(signal_index, bool):
        return None
    if signal_index < 0 or signal_index + 1 >= len(prices):
        return None
    if not horizons or any(not isinstance(h, int) or isinstance(h, bool) or h < 1 for h in horizons):
        return None
    if (not isinstance(roundtrip_cost_bps, (int, float)) or isinstance(roundtrip_cost_bps, bool)
            or not math.isfinite(roundtrip_cost_bps) or roundtrip_cost_bps < 0
            or roundtrip_cost_bps >= 10000):
        return None
    if any(not isinstance(row, dict) or any(not _price(row.get(k)) for k in ("open", "high", "low", "close")) or row["low"] > min(row["open"], row["close"]) or row["high"] < max(row["open"], row["close"]) for row in prices):
        return None
    # Require ISO dates in strictly increasing session order.
    try:
        dates = [date.fromisoformat(row["date"]) for row in prices]
    except (KeyError, ValueError, TypeError):
        return None
    if any(not isinstance(row["date"], str) or row["date"] != d.isoformat()
           for row, d in zip(prices, dates)):
        return None
    if any(later <= earlier for earlier, later in zip(dates, dates[1:])):
        return None
    # Flag large close-to-next-open jumps for review, never silently discard.
    entry = prices[signal_index + 1]["open"]
    entry_gap_pct = (entry / prices[signal_index]["close"] - 1) * 100
    result = {"entry_open": entry, "price_source": price_metadata["source"],
              "currency": price_metadata["currency"],
              "entry_gap_pct": round(entry_gap_pct, 4),
              "large_entry_gap_review": abs(entry_gap_pct) >= 20,
              "roundtrip_cost_bps": roundtrip_cost_bps, "horizons": {},
              "research_only": True, "trade_ready": False,
              "data_provenance_independently_verified": False}
    for horizon in horizons:
        end = signal_index + horizon
        if end >= len(prices):
            result["horizons"][horizon] = None
            continue
        # Includes the next session through the horizon-th future session.
        window = prices[signal_index + 1:end + 1]
        gross_return = (window[-1]["close"] / entry - 1) * 100
        gaps = [(prices[k]["open"] / prices[k - 1]["close"] - 1) * 100
                for k in range(signal_index + 1, end + 1)]
        result["horizons"][horizon] = {
            "close_return_pct": round(gross_return, 4),
            "largest_overnight_gap_pct": round(max(gaps, key=abs), 4),
            "large_gap_review": any(abs(gap) >= 20 for gap in gaps),
            "manual_review_required": any(abs(gap) >= 20 for gap in gaps),
            "estimated_net_close_return_pct": round(gross_return - roundtrip_cost_bps / 100, 4),
            "max_favorable_pct": round((max(r["high"] for r in window) / entry - 1) * 100, 4),
            "max_adverse_pct": round((min(r["low"] for r in window) / entry - 1) * 100, 4),
        }
    return result
