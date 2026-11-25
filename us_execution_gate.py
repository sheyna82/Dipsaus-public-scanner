"""Evaluate manually verified US research at the first meaningful resistance."""
from datetime import datetime, timezone

from eu_entry_net import DISABLED, age_seconds
from research_net_bridge import evaluate_verified_research_evidence
from us_yahoo_bars import number

REQUIRED = ('symbol', 'quote_utc', 'ask_usd', 'bid_usd', 'eur_per_usd', 'fx_utc',
            'invalidation_usd', 'first_meaningful_resistance_usd',
            'bottom_confirmed', 'daily_weekly_reviewed', 'resistance_confirmed',
            'company_event_risk_verified', 'recent_price_moving_news_verified',
            'upcoming_material_events_verified', 'corporate_actions_verified',
            'portfolio_fit_verified', 'broker_quote_verified', 'fx_verified',
            'buy_fee_eur', 'sell_fee_eur', 'fees_verified', 'fx_buy_fee_rate', 'fx_sell_fee_rate',
            'buy_slippage_per_share', 'sell_slippage_per_share', 'slippage_verified')


def evaluate_trade(evidence, now=None, budget_eur=3500, max_risk_eur=None):
    """Return a non-executable research calculation with independently supplied inputs."""
    now = now or datetime.now(timezone.utc)
    missing = [field for field in REQUIRED if evidence.get(field) is None]
    if missing:
        return {**DISABLED, 'status': 'DATA_BLOCKED', 'missing': missing}
    flags = [field for field in REQUIRED if field.endswith(('_verified', '_confirmed', '_reviewed'))]
    unverified = [field for field in flags if evidence[field] is not True]
    if unverified:
        return {**DISABLED, 'status': 'REVIEW_BLOCKED', 'unverified': unverified}
    ages = [age_seconds(evidence[field], now) for field in ('quote_utc', 'fx_utc')]
    if any(age is None or not 0 <= age <= limit for age, limit in zip(ages, (120, 300))):
        return {**DISABLED, 'status': 'STALE_OR_FUTURE_DATA', 'ages_seconds': ages}
    risk_cap = max_risk_eur if number(max_risk_eur) and max_risk_eur > 0 else None
    result = evaluate_verified_research_evidence({
        **evidence, 'broker_ask': evidence['ask_usd'], 'broker_bid': evidence['bid_usd'],
        'invalidation': evidence['invalidation_usd'], 'target': evidence['first_meaningful_resistance_usd'],
        'fx_eur_per_unit': evidence['eur_per_usd'], 'levels_verified': True, 'quote_freshness_verified': True,
    }, market='US', budget_eur=budget_eur, max_risk_eur=risk_cap)
    if 'checks' not in result:
        return result
    checks = {**result['checks'], 'risk_within_cap': result['checks'].get('net_risk_within_cap') is True}
    return {**result, 'status': 'HUMAN_REVIEW_REQUIRED' if all(checks.values()) else 'MONEY_OR_RISK_BLOCKED',
            'symbol': evidence['symbol'], 'whole_shares': result['shares'], 'checks': checks}
