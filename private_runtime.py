"""Private configuration and state; never write runtime data to public Git/artifacts."""
import base64
import json
import os
from pathlib import Path
import urllib.request
import urllib.error

CONFIG_NAMES = {
    'manual_recovery_triggers.json', 'manual_recovery_triggers_supplemental.json',
    'portfolio_reentry_watch.json', 'profit_exit_watch.json',
    'notification_quality_gate.json', 'us_live_trigger_routes.json',
    'prealert_notification_state.json',
}


SECRET_CONFIG = {
    'SCANNER_MANUAL_TRIGGERS': 'manual_recovery_triggers.json',
    'SCANNER_SUPPLEMENTAL_TRIGGERS': 'manual_recovery_triggers_supplemental.json',
    'SCANNER_PORTFOLIO_WATCH': 'portfolio_reentry_watch.json',
    'SCANNER_PROFIT_WATCH': 'profit_exit_watch.json',
    'SCANNER_NOTIFICATION_GATE': 'notification_quality_gate.json',
}


def hydrate(raw=None):
    # Split Secrets stay below GitHub's per-Secret size limit.
    if raw is not None:
        bundle = json.loads(raw)
    else:
        bundle = {}
        for key, name in SECRET_CONFIG.items():
            if os.environ.get(key):
                try:
                    bundle[name] = json.loads(os.environ[key])
                except (json.JSONDecodeError, TypeError):
                    raise RuntimeError('PRIVATE_CONFIG_INVALID_JSON_' + key) from None
    if not bundle:
        raise RuntimeError('PRIVATE_CONFIG_NOT_CONFIGURED')
    if not isinstance(bundle, dict) or set(bundle) - CONFIG_NAMES:
        raise RuntimeError('PRIVATE_CONFIG_INVALID')
    required = {'manual_recovery_triggers.json', 'profit_exit_watch.json',
                'portfolio_reentry_watch.json', 'notification_quality_gate.json'}
    if not required.issubset(bundle):
        raise RuntimeError('PRIVATE_CONFIG_INCOMPLETE')
    Path('config').mkdir(exist_ok=True)
    for name, value in bundle.items():
        if not isinstance(value, dict):
            raise RuntimeError('PRIVATE_CONFIG_INVALID')
        (Path('config') / name).write_text(json.dumps(value))


class PrivateStore:
    def __init__(self, mode="prealert"):
        if mode not in ("prealert", "eu", "us"): raise RuntimeError("STATE_MODE_INVALID")
        self.repo = os.environ.get('SCANNER_STATE_REPOSITORY', '').strip()
        self.token = os.environ.get('SCANNER_STATE_TOKEN', '').strip()
        if not self.repo or not self.token:
            raise RuntimeError('PRIVATE_STATE_NOT_CONFIGURED')
        self.sha = None
        self.path = 'migration_runtime/public_scanner_' + mode + '_state.json'
        self.metadata = self.request('')
        if self.metadata.get('private') is not True:
            raise RuntimeError('STATE_REPOSITORY_MUST_BE_PRIVATE')

    def request(self, suffix, data=None, accept='application/vnd.github+json'):
        req = urllib.request.Request('https://api.github.com/repos/' + self.repo + suffix,
            data=json.dumps(data).encode() if data is not None else None,
            method='PUT' if data is not None else 'GET',
            headers={'Authorization': 'Bearer ' + self.token,
                     'Accept': accept,
                     'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.load(res)
        except urllib.error.HTTPError as exc:
            stage = 'METADATA' if not suffix else ('SAVE' if data is not None else 'READ')
            raise RuntimeError(f'PRIVATE_STATE_REQUEST_FAILED_{stage}_HTTP_{exc.code}') from None
        except Exception:
            # Never echo authenticated URLs, payloads or provider exception strings.
            raise RuntimeError('PRIVATE_STATE_REQUEST_FAILED') from None

    def load(self):
        # A missing state must be initialized explicitly; never silently reset deduplication.
        record = self.request('/contents/' + self.path)
        self.sha = record['sha']
        try:
            if record.get('encoding') == 'none':
                state = self.request('/contents/' + self.path, accept='application/vnd.github.raw+json')
            else:
                state = json.loads(base64.b64decode(record['content']))
        except (ValueError, TypeError):
            raise RuntimeError('PRIVATE_STATE_INVALID_JSON') from None
        if not isinstance(state.get('signals'), dict):
            raise RuntimeError('PRIVATE_STATE_INVALID')
        return state

    def save(self, state):
        record = self.request('/contents/' + self.path, {
            'message': 'Persist scanner runtime state', 'sha': self.sha,
            'content': base64.b64encode(json.dumps(state).encode()).decode(),
            'branch': self.metadata['default_branch']})
        self.sha = record['content']['sha']

    def require_exclusive_sender(self):
        workflows = self.request('/actions/workflows?per_page=100')
        if workflows.get('total_count', 101) > 100:
            raise RuntimeError('PRIVATE_WORKFLOW_COVERAGE_UNKNOWN')
        # Every old workflow must be disabled before enabling the new notification owner.
        if any(w.get('state') == 'active' for w in workflows.get('workflows', [])):
            raise RuntimeError('PRIVATE_SCANNER_STILL_ACTIVE')
        for status in ('queued', 'in_progress', 'waiting', 'pending', 'requested'):
            if self.request('/actions/runs?per_page=1&status=' + status).get('total_count'):
                raise RuntimeError('PRIVATE_SCANNER_RUN_STILL_PENDING')
