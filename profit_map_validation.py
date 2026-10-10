"""Validate private profit zones without comparing different currencies."""
import math


def zone(item, currency, name, legacy=None):
    suffix = str(currency or '').lower()
    if suffix not in ('eur', 'usd'):
        return None
    mapping = item.get('profit_map') or {}
    value = item.get(f'{name}_{suffix}') or mapping.get(f'{name}_{suffix}')
    if value is None and legacy:
        value = item.get(f'{legacy}_{suffix}') or mapping.get(f'{legacy}_{suffix}')
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return None
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v <= 0 for v in value):
        return None
    return list(value) if value[0] <= value[1] else None


def assess(item, currency):
    names = ('first_friction', 'first_meaningful_resistance', 'further_recovery_zone')
    zones = {name: zone(item, currency, name, 'first_decision_zone' if name == 'first_friction' else None) for name in names}
    missing = [name for name, value in zones.items() if value is None]
    if not missing and not (zones[names[0]][0] <= zones[names[1]][0] <= zones[names[2]][0]):
        missing.append('ordered_recovery_zones')
    mapping = item.get('profit_map') or {}
    profits = mapping.get('gross_profit_eur_at_zones')
    if not isinstance(profits, dict) or any(isinstance(profits.get(name), bool) or not isinstance(profits.get(name), (int, float)) or not math.isfinite(profits[name]) for name in names):
        missing.append('gross_profit_eur_at_zones')
    # EUR amounts must be supplied from verified holdings/FX; never infer from USD quotes.
    return {'status': 'INCOMPLETE' if missing else 'COMPLETE', 'missing': missing, 'currency': currency}
