"""Reconcile independent research lanes in the existing private US route report."""
from datetime import date, datetime, timezone

from eu_entry_net import age_seconds

LANES = ('fast', 'deep')
EVIDENCE_MAX_AGE = 7 * 86400
RECORD_MAX_AGE = 14 * 86400
QUALIFIED, DEFERRED = 'QUALIFIED', 'QUALIFIED_DEFERRED'
REJECTED, UNAVAILABLE, NOT_SCANNED = 'REJECTED', 'DATA_UNAVAILABLE', 'NOT_SCANNED'
REVOKED, INVALIDATED, EXPIRED = 'REVOKED', 'INVALIDATED', 'EXPIRED'
TERMINAL = {REJECTED, REVOKED, INVALIDATED}


def qualification_age(record, now):
    qualification = record.get('qualification')
    return age_seconds(qualification.get('utc'), now) if isinstance(qualification, dict) else None


def fresh_evidence(evidence, stamp, now):
    age = age_seconds(stamp, now)
    if not isinstance(evidence, dict) or age is None or not 0 <= age <= EVIDENCE_MAX_AGE:
        return False
    day = evidence.get('last_bar_date')
    if day is not None:
        try:
            return 0 <= (now.date() - date.fromisoformat(day)).days <= EVIDENCE_MAX_AGE // 86400
        except (TypeError, ValueError):
            return False
    return True


def active_qualification(record, now):
    if record.get('status') in TERMINAL or record.get('qualification_retired') is True:
        return False
    qualification = record.get('qualification') or {}
    return fresh_evidence(qualification.get('evidence'), qualification.get('utc'), now)


def new_record(previous, status, observed, evidence, *, now, reason=None):
    """Only a new positive observation can renew qualification time."""
    previous = previous or {}
    age = age_seconds(observed, now)
    old_age = age_seconds(previous.get('observed_utc'), now)
    if (age is None or age < 0 or (old_age is not None and (age > old_age
            or (age == old_age and status not in (REVOKED, INVALIDATED))))):
        return previous
    qualification = previous.get('qualification')
    retired = previous.get('retirement_reason')
    retired_at = previous.get('retired_utc')
    retirement_detail = previous.get('retirement_detail')
    if status == QUALIFIED:
        # A fast candidate can be processed long after its minute evidence was
        # sampled. Retain the actual source timestamp for its original rights.
        stamp = observed
        minute = (evidence or {}).get('completed_minute_bar') or {}
        if type(minute.get('ts')) is int:
            stamp = datetime.fromtimestamp(minute['ts'], timezone.utc).isoformat()
            source_age = age_seconds(stamp, now)
            if source_age is None or source_age < age or source_age - age > 120:
                return new_record(previous, UNAVAILABLE, observed, evidence, now=now)
        qualification = {'utc': stamp, 'evidence': evidence, 'original_outcome': status}
        retired = retired_at = retirement_detail = None
    elif status in TERMINAL:
        retired, retired_at, retirement_detail = status, observed, reason
    record = {'status': status, 'observed_utc': observed, 'qualification': qualification,
              'qualification_retired': retired is not None, 'retirement_reason': retired, 'retired_utc': retired_at,
              'retirement_detail': retirement_detail,
              'evidence': evidence if evidence else previous.get('evidence'),
              'evidence_observed_utc': observed if evidence else previous.get('evidence_observed_utc')}
    # A previously observed issuer mismatch persists until an actual new identity check.
    identity = (evidence or {}).get('identity_status')
    record['identity_disputed'] = identity == 'IDENTITY_MISMATCH' or (
        identity != 'NAME_CONSISTENT_UNVERIFIED' and previous.get('identity_disputed') is True)
    return record


def load_registry(report, *, now):
    if isinstance(report.get('lane_registry'), dict):
        return {symbol: {lane: {**record, 'evidence_observed_utc': record.get('evidence_observed_utc') or record.get('observed_utc')}
                         for lane, record in lanes.items() if lane in LANES and isinstance(record, dict)}
                for symbol, lanes in report['lane_registry'].items() if isinstance(lanes, dict)}
    # Upgrade existing route rows without re-dating historical evidence.
    registry = {}
    for row in report.get('rows', []):
        for lane, evidence in row.get('discovery_evidence', {}).items():
            if lane not in LANES or not isinstance(evidence, dict):
                continue
            observed = evidence.get('observed_utc') or row.get('observed_utc') or report.get('generated_utc')
            status = (REVOKED if evidence.get('identity_status') == 'IDENTITY_MISMATCH' else
                      QUALIFIED if evidence.get('auto_promoted') is True else DEFERRED)
            record = new_record(None, status, observed, evidence, now=now)
            if record:
                registry.setdefault(row['symbol'], {})[lane] = record
    return registry


def reconcile(previous, events, *, now, revoked=(), failed_batches=(), fast_failed=False):
    registry = load_registry(previous, now=now)
    statuses = {}
    for symbol in sorted(registry.keys() | events.keys()):
        lanes = registry.setdefault(symbol, {})
        statuses[symbol] = {}
        for lane in LANES:
            old = lanes.get(lane, {})
            updates = events.get(symbol, {}).get(lane, [])
            source_batch = (old.get('evidence') or {}).get('source_batch')
            if symbol in revoked and (updates or old):
                updates = [{'status': REVOKED, 'observed_utc': now.isoformat()}]
            elif not updates and old and (fast_failed if lane == 'fast' else source_batch in failed_batches):
                updates = [{'status': UNAVAILABLE, 'observed_utc': now.isoformat()}]
            # A retry preserves a substantive result from the same sweep if
            # the newer attempt is merely missing data for this instrument.
            substantive = [update for update in updates if update['status'] != UNAVAILABLE]
            updates = substantive or updates
            verdict = NOT_SCANNED
            record = old
            for update in sorted(updates, key=lambda item: -age_seconds(item['observed_utc'], now)):
                verdict = update['status']
                if record or update.get('evidence') or verdict == REVOKED:
                    updated = new_record(record, verdict, update['observed_utc'], update.get('evidence'),
                                         now=now, reason=update.get('reason'))
                    if updated is not record and updated:
                        verdict = updated['status']
                    record = updated
            if record:
                lanes[lane] = record
            record = lanes.get(lane)
            age = age_seconds(record.get('observed_utc'), now) if record else None
            qualified_age = qualification_age(record, now) if record else None
            evidence_age = age_seconds(record.get('evidence_observed_utc'), now) if record else None
            if record and (age is None or age < 0 or age > RECORD_MAX_AGE
                           or (verdict == UNAVAILABLE and evidence_age is not None and evidence_age > RECORD_MAX_AGE)):
                del lanes[lane]
            expired = record and not record.get('qualification_retired') and qualified_age is not None and not active_qualification(record, now)
            statuses[symbol][lane] = EXPIRED if expired else verdict
        if not lanes:
            del registry[symbol]
    return registry, statuses
