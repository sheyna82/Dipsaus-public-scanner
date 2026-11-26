"""Conservative capacity check for an independently reviewed research scenario."""
import hashlib
import json
from decimal import Decimal
from math import isfinite

CAPITAL_EUR = Decimal(50_000)
POSITION_LIMIT = 6
PORTFOLIO_MAX_AGE_SECONDS = 120


def amount(value):
    try:
        return Decimal(str(value)) if type(value) in (int, float) and isfinite(value) and value >= 0 else None
    except OverflowError:
        return None


def holdings_digest(positions):
    """Bind reviewed account totals to every current canonical position, including aliases."""
    if not isinstance(positions, dict):
        return None
    rows = []
    for key, position in positions.items():
        if not isinstance(key, str) or not key or not isinstance(position, dict):
            return None
        symbol = position.get('provider_symbol') or key
        shares = amount(position.get('shares'))
        if not isinstance(symbol, str) or not symbol or shares is None or not shares:
            return None
        shares_text = format(shares, 'f')
        if '.' in shares_text:
            shares_text = shares_text.rstrip('0').rstrip('.')
        rows.append([key, symbol, shares_text])
    payload = json.dumps(sorted(rows), ensure_ascii=False, separators=(',', ':')).encode()
    return hashlib.sha256(b'DIPSAUS_CANONICAL_HOLDINGS_V1\x00' + payload).hexdigest()


def check_capacity(symbol, portfolio, positions, acquisition_eur, *, now, commitments=()):
    from eu_entry_net import age_seconds

    digest = holdings_digest(positions)
    if digest is None:
        return {'status': 'CANONICAL_HOLDINGS_UNAVAILABLE'}
    if not isinstance(portfolio, dict) or portfolio.get('source') != 'DEGIRO' or portfolio.get('currency') != 'EUR':
        return {'status': 'REVIEWED_CAPACITY_UNAVAILABLE'}
    age = age_seconds(portfolio.get('observed_utc'), now)
    if age is None or not 0 <= age <= PORTFOLIO_MAX_AGE_SECONDS:
        return {'status': 'REVIEWED_CAPACITY_STALE_OR_FUTURE'}
    if portfolio.get('holdings_sha256') != digest:
        return {'status': 'CAPACITY_HOLDINGS_MISMATCH'}
    exposure = amount(portfolio.get('open_exposure_eur'))
    pending = amount(portfolio.get('pending_buy_eur'))
    cash = amount(portfolio.get('available_cash_eur'))
    acquisition = amount(acquisition_eur)
    pending_slots = portfolio.get('pending_new_positions')
    if (None in (exposure, pending, cash, acquisition) or acquisition <= 0
            or (positions and exposure <= 0) or (not positions and exposure != 0)
            or type(pending_slots) is not int or pending_slots < 0 or (pending_slots and not pending)):
        return {'status': 'INVALID_CAPACITY_AMOUNTS'}
    held = [key for key, item in positions.items() if (item.get('provider_symbol') or key) == symbol]
    if len(held) > 1:
        return {'status': 'AMBIGUOUS_POSITION_IDENTITY'}
    # An updated snapshot may reflect an unrelated sale. Keep outstanding
    # advice charged until the existing day ends or that exact reservation is released.
    used = tuple(commitments)
    advised = Decimal(0)
    for item in used:
        if not isinstance(item, dict) or item.get('status') != 'CAPACITY_VERIFIED' or type(item.get('new_position')) is not bool:
            return {'status': 'CAPACITY_RESERVATIONS_UNVERIFIED'}
        required = amount(item.get('required_eur'))
        if not required:
            return {'status': 'CAPACITY_RESERVATIONS_UNVERIFIED'}
        advised += required
    opening = not held
    slots = len(positions) + pending_slots + sum(item.get('new_position') is True for item in used) + int(opening)
    if slots > POSITION_LIMIT:
        return {'status': 'POSITION_LIMIT_EXCEEDED'}
    if exposure + pending + advised + acquisition > CAPITAL_EUR:
        return {'status': 'CAPITAL_LIMIT_EXCEEDED'}
    if advised + acquisition > cash:
        return {'status': 'AVAILABLE_CASH_INSUFFICIENT'}
    return {'status': 'CAPACITY_VERIFIED', 'holdings_sha256': digest, 'new_position': opening,
            'required_eur': float(acquisition)}
