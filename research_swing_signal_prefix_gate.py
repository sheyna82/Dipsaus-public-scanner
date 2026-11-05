"""Research-only prefix consistency gate inspired by Freqtrade lookahead analysis.

A causal signal calculator must give the same historical scores when called
with a full history or with only information available at each date.
No external dependencies, no trading, no copying of third-party code.
"""
from decimal import Decimal, InvalidOperation


def _finite(value):
    if isinstance(value, bool):
        raise ValueError("invalid_signal_value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError("invalid_signal_value") from None
    if not result.is_finite():
        raise ValueError("invalid_signal_value")
    return result


def validate_signal_prefix_consistency(bars, signal_calculator, *, min_history=2):
    if not isinstance(bars, (list, tuple)) or len(bars) < min_history:
        raise ValueError("insufficient_signal_history")
    if not callable(signal_calculator):
        raise ValueError("invalid_signal_calculator")
    # Each input receives a fresh copy, preventing in-place mutations from
    # polluting subsequent comparisons.
    from copy import deepcopy
    full = signal_calculator(deepcopy(list(bars)))
    if not isinstance(full, (list, tuple)) or len(full) != len(bars):
        raise ValueError("invalid_full_signal_output")
    violations = []
    for count in range(min_history, len(bars) + 1):
        prefix = signal_calculator(deepcopy(list(bars[:count])))
        if not isinstance(prefix, (list, tuple)) or len(prefix) != count:
            raise ValueError("invalid_prefix_signal_output")
        for index in range(min_history - 1, count):
            if _finite(prefix[index]) != _finite(full[index]):
                violations.append({"index": index, "prefix_length": count})
    return {
        "research_only": True,
        "lookahead_prefix_consistent": not violations,
        "violations": violations,
        "bars_checked": len(bars),
        "causal_execution_proven": False,
        "market_data_authenticity_verified": False,
    }
