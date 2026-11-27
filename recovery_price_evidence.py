"""Research price evidence shared by monitoring and the financial gate."""
import math


def positive_price(value):
    try:
        return type(value) in (int, float) and 0 < value and math.isfinite(value)
    except OverflowError:
        return False


def resistance_room(level, price, *, price_basis):
    """A single first resistance. Never substitute a farther historical target."""
    result = {'status': 'UNAVAILABLE', 'level': level if positive_price(level) else None,
              'price_basis': price_basis, 'remaining_pct': None}
    if not positive_price(price) or result['level'] is None:
        return result
    if level <= price:
        return {**result, 'status': 'PASSED' if level < price else 'REACHED'}
    # Calculate before rounding so a small positive distance does not become a passed level.
    distance = (level - price) / price * 100
    return {**result, 'status': 'AHEAD', 'remaining_pct': distance} if math.isfinite(distance) else result


def level_observations(bars, level, after):
    """Observe a cross, a subsequent hold and a subsequent retest of one level."""
    if not positive_price(level) or type(after) is not int:
        return {}
    proof, previous = {}, None
    for bar in bars:
        ts, close, low = (bar[field] for field in ('ts', 'close', 'low'))
        if previous is not None and ts != previous['ts'] + 60:
            proof, previous = {}, None
        if close < level:
            proof = {}
        if ts > after:
            point = {'ts': ts, 'close': close, 'low': low}
            if not proof and previous is not None and previous['close'] <= level < close:
                proof = {'level': level, 'breakout': point}
            elif proof and 'hold' not in proof and low > level:
                proof['hold'] = point
            elif 'hold' in proof and 'retest' not in proof and low <= level <= close:
                proof['retest'] = point
        previous = bar
    return proof


def breakout_stage(proof, last_ts, last_close):
    """Fail closed on legacy flags, unsupported prices and unordered evidence."""
    if not isinstance(proof, dict) or not positive_price(proof.get('level')):
        return None
    level = proof['level']
    if type(last_ts) is not int or not positive_price(last_close) or last_close < level:
        return None
    last = 0
    stage = None
    for name in ('breakout', 'hold', 'retest'):
        point = proof.get(name)
        if not isinstance(point, dict):
            break
        ts, close, low = (point.get(field) for field in ('ts', 'close', 'low'))
        if (type(ts) is not int or ts % 60 or not last < ts <= last_ts
                or not positive_price(close) or not positive_price(low) or not low <= close):
            break
        if not {'breakout': close > level, 'hold': low > level, 'retest': low <= level <= close}[name]:
            break
        last, stage = ts, name
    return stage
