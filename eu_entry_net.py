"""Bind EU recovery research to independently reviewed private entry evidence."""
import base64
import hashlib
import hmac
import json
import re
from datetime import datetime, timedelta

from recovery_portfolio_capacity import check_capacity
from recovery_price_evidence import resistance_room
from research_ed25519_verifier import verify_ed25519_batch
from research_instrument_gate import isin_checksum_valid
from research_net_attestation import MAX_AGE_SECONDS, evaluate_attested_scenario

EARLY_RECOVERY = 'EARLY_RECOVERY'
DEGIRO_VERIFICATION = 'DEGIRO_VERIFICATION'
FINANCIAL_ENTRY_CONFIRMED = 'FINANCIAL_ENTRY_CONFIRMED'
PHASE_RANK = {EARLY_RECOVERY: 1, DEGIRO_VERIFICATION: 2, FINANCIAL_ENTRY_CONFIRMED: 3}
DISABLED = {'trade_ready': False, 'order_placement_enabled': False}
REVIEWER_PIN_ENV = 'DIPSAUS_EU_ENTRY_REVIEWER_SHA256'
EVIDENCE_STATE_KEY = 'eu_verified_entry_inputs'


def age_seconds(timestamp, now):
    if isinstance(timestamp, str):
        try:
            parsed = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            if parsed.utcoffset() is not None:
                return (now - parsed).total_seconds()
        except (ValueError, TypeError, OverflowError):
            pass
    return None


def evidence_digest(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return hashlib.sha256(b'DIPSAUS_EU_ENTRY_REVIEW_V1\x00' + encoded).hexdigest()


def evaluate_entry(symbol, currency, envelope, *, now, reviewer_pin, positions=None, commitments=()):
    """Only independently reviewed inputs signed by the pinned reviewer qualify."""
    blocked = {**DISABLED, 'status': 'DATA_BLOCKED'}
    if not isinstance(envelope, dict) or not envelope:
        return {**blocked, 'reason': 'NO_INDEPENDENT_BROKER_EVIDENCE'}
    if not isinstance(reviewer_pin, str) or not re.fullmatch(r'[0-9a-f]{64}', reviewer_pin):
        return {**blocked, 'reason': 'NO_TRUSTED_REVIEWER'}
    try:
        payload = envelope['payload']
        public_key = envelope['public_key_pem'].encode('ascii')
        signature = base64.b64decode(envelope['signature_b64'], validate=True)
        digest = evidence_digest(payload)
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return {**blocked, 'reason': 'INVALID_BROKER_EVIDENCE_ENVELOPE'}
    if not hmac.compare_digest(hashlib.sha256(public_key).hexdigest(), reviewer_pin):
        return {**blocked, 'reason': 'REVIEWER_KEY_MISMATCH'}
    if not isinstance(payload, dict) or payload.get('independently_reviewed') is not True:
        return {**blocked, 'reason': 'INDEPENDENT_REVIEW_MISSING'}
    instrument, quote = payload.get('instrument'), payload.get('quote')
    if not isinstance(instrument, dict) or not isinstance(quote, dict):
        return {**blocked, 'reason': 'INSTRUMENT_OR_QUOTE_MISSING'}
    isin, mic = instrument.get('isin'), instrument.get('operating_mic')
    if (instrument.get('symbol') != symbol or instrument.get('identity_verified') is not True
            or not isin_checksum_valid(isin) or not isinstance(mic, str)
            or not re.fullmatch(r'[A-Z0-9]{4}', mic)
            or quote.get('symbol') != symbol or quote.get('isin') != isin
            or quote.get('operating_mic') != mic):
        return {**blocked, 'reason': 'INSTRUMENT_IDENTITY_UNVERIFIED_OR_MISMATCHED'}
    if currency != 'EUR' or instrument.get('currency') != 'EUR' or quote.get('currency') != 'EUR':
        return {**blocked, 'reason': 'EUR_LISTING_REQUIRED'}
    if quote.get('source') != 'DEGIRO' or payload.get('target_kind') != 'FIRST_MEANINGFUL_RESISTANCE':
        return {**blocked, 'reason': 'BROKER_SOURCE_OR_FIRST_RESISTANCE_UNVERIFIED'}
    observed = quote.get('observed_utc')
    age = age_seconds(observed, now)
    if age is None or not 0 <= age <= 120:
        return {**blocked, 'reason': 'BROKER_QUOTE_STALE_OR_FUTURE'}
    market_age = age_seconds(quote.get('market_utc'), now)
    if quote.get('market_data_mode') != 'REALTIME' or market_age is None or not age <= market_age <= 120:
        return {**blocked, 'reason': 'BROKER_MARKET_TIMESTAMP_UNVERIFIED_OR_DELAYED'}
    attestations, inputs = payload.get('attestations'), payload.get('inputs')
    if not isinstance(attestations, dict) or not isinstance(inputs, dict):
        return {**blocked, 'reason': 'BROKER_INPUTS_OR_ATTESTATIONS_MISSING'}
    if any(type(inputs.get(field)) not in (int, float) or inputs[field] != value
           for field, value in (('fx_eur_per_unit', 1), ('fx_buy_fee_rate', 0), ('fx_sell_fee_rate', 0))):
        return {**blocked, 'reason': 'EXPLICIT_EUR_COSTS_REQUIRED'}
    quote_attestation = attestations.get('broker_quote')
    if (not isinstance(quote_attestation, dict) or quote_attestation.get('source_id') != 'DEGIRO'
            or quote_attestation.get('observed_utc') != observed):
        return {**blocked, 'reason': 'BROKER_QUOTE_ATTESTATION_MISMATCH'}
    for group, limit in MAX_AGE_SECONDS.items():
        item = attestations.get(group)
        group_age = age_seconds(item.get('observed_utc'), now) if isinstance(item, dict) else None
        if group_age is None or not 0 <= group_age <= limit:
            return {**blocked, 'reason': 'EVIDENCE_STALE_OR_FUTURE', 'group': group}
    verification = verify_ed25519_batch(digest, signature, public_key)
    if verification.get('cryptographic_signature_valid') is not True:
        return {**blocked, 'reason': 'BROKER_REVIEW_SIGNATURE_UNVERIFIED'}
    evidence = {**inputs, 'broker_bid': quote.get('bid'), 'broker_ask': quote.get('ask')}
    result = evaluate_attested_scenario(evidence, attestations, market='EU', now=now)
    checked_target = inputs.get('target') if result.get('attestation_metadata_checked') is True else None
    resistance = resistance_room(checked_target, quote.get('ask'), price_basis='DEGIRO_ASK')
    # The pinned reviewer authenticates the independent review, while the
    # input attestations and the bridge still verify each individual assertion.
    capacity = {}
    if result['status'] == 'HUMAN_REVIEW_REQUIRED':
        horizon = payload.get('planned_holding_trading_days')
        if type(horizon) is int and 5 <= horizon <= 15:
            capacity = check_capacity(symbol, payload.get('portfolio'), positions, result.get('capacity_required_eur'),
                                      now=now, commitments=commitments)
        else:
            capacity = {'status': 'HOLDING_HORIZON_UNVERIFIED'}
    return {**result, 'independent_review_signature_verified': True, 'portfolio_capacity': capacity,
            'resistance_room': resistance}


def recovery_phase(row, financial, *, now):
    """Recheck the raw timestamps before a report can produce an alert."""
    if row.get('trade_ready') is not False or row.get('order_placement_enabled') is not False:
        return None
    flags = row.get('historical_flags')
    if (row.get('early_recovery_watch') is not True or not isinstance(flags, list)
            or 'STALE-DATA' in flags or row.get('intraday_evidence') not in (
                'EARLY-STRUCTURE-OBSERVED', 'NO-COMBINED-15M-CONFIRMATION')):
        return None
    age = age_seconds(row.get('last_15m_bar'), now)
    if age is None or not 0 <= age <= timedelta(minutes=45).total_seconds():
        return None
    if (financial.get('status') == 'HUMAN_REVIEW_REQUIRED'
            and (financial.get('resistance_room') or {}).get('status') == 'AHEAD'
            and (financial.get('portfolio_capacity') or {}).get('status') == 'CAPACITY_VERIFIED'
            and row.get('intraday_evidence') == 'EARLY-STRUCTURE-OBSERVED'):
        return FINANCIAL_ENTRY_CONFIRMED
    quote_age = age_seconds(row.get('provider_1m_quote_utc'), now)
    if (row.get('broker_verify_now') is True and row.get('broker_check_candidate') is True
            and (row.get('provider_freshness_pass') is True
                 or row.get('provider_delayed_but_usable_for_attention') is True)
            and quote_age is not None and 0 <= quote_age <= 1200):
        return DEGIRO_VERIFICATION
    return EARLY_RECOVERY


def assess_report(report, evidence_by_symbol, *, now, reviewer_pin=None, positions=None, commitments=()):
    """Evaluate a private report without trusting any financial claim in its rows."""
    from dipsaus_eu_freshness import classify_eu_report

    freshness = classify_eu_report(report, now=now)
    if not freshness['fresh']:
        return freshness, []
    rows = report.get('candidates')
    if not isinstance(rows, list) or any(
            not isinstance(row, dict) or not isinstance(row.get('symbol'), str)
            or not re.fullmatch(r'[A-Z0-9][A-Z0-9.\-]{0,23}', row['symbol']) for row in rows):
        return {'fresh': False, 'reason': 'INVALID_CANDIDATE_SCHEMA'}, []
    if len({row['symbol'] for row in rows}) != len(rows):
        return {'fresh': False, 'reason': 'DUPLICATE_REPORT_INSTRUMENT'}, []
    evidence_by_symbol = evidence_by_symbol if isinstance(evidence_by_symbol, dict) else {}
    evaluated = []
    for row in rows:
        symbol = row['symbol']
        result = evaluate_entry(symbol, row.get('currency'), evidence_by_symbol.get(symbol),
                                now=now, reviewer_pin=reviewer_pin, positions=positions, commitments=commitments)
        evaluated.append({**row, 'financial_entry': result,
                          'recovery_phase': recovery_phase(row, result, now=now)})
    return freshness, evaluated
