"""Observe a new recovery against a contiguous, completed minute series."""
from statistics import median


def intraday_structure(rows):
    if len(rows) < 12:
        return {'available': False, 'quality': False, 'early_recovery_observed': False}
    recent = rows[-45:]
    earlier, retest = recent[:-5], recent[-5:]
    bottom_index = min(range(len(earlier)), key=lambda index: earlier[index]['low'])
    bottom = earlier[bottom_index]
    rebound_bars = earlier[bottom_index + 1:]
    result = {'available': True, 'quality': False, 'early_recovery_observed': False,
              'recovery_low': bottom['low'], 'recovery_low_ts': bottom['ts']}
    if len(rebound_bars) < 3:
        return result
    peak = max(bar['high'] for bar in rebound_bars)
    higher_low = min(bar['low'] for bar in retest)
    price = recent[-1]['close']
    rebound = 100 * (price / bottom['low'] - 1)
    reclaim = price >= peak * 0.997
    early = (higher_low > bottom['low'] and rebound >= 0.35
             and price > median(bar['close'] for bar in retest[:-1]))
    closes = [bar['close'] for bar in recent[bottom_index + 1:]]
    travel = sum(abs(end - start) for start, end in zip(closes, closes[1:]))
    efficiency = abs(closes[-1] - closes[0]) / travel if travel else 0
    quality = (early and reclaim and peak >= bottom['low'] * 1.008
               and higher_low >= bottom['low'] * 1.0025 and efficiency >= 0.12)
    return {**result, 'quality': quality, 'early_recovery_observed': early,
            'first_rebound_high': peak, 'higher_low': higher_low,
            'reclaim_observed': reclaim, 'rebound_pct': rebound,
            'path_efficiency': efficiency}
