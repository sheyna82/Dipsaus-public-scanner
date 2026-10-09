"""Private configuration and state; never write runtime data to public Git/artifacts."""
import base64
import json
import os
from pathlib import Path
import urllib.request

CONFIG_NAMES = {
    'manual_recovery_triggers.json', 'manual_recovery_triggers_supplemental.json',
    'portfolio_reentry_watch.json', 'profit_exit_watch.json',
    'notification_quality_gate.json', 'us_live_trigger_routes.json',
    'prealert_notification_state.json', 'fcx_2026-10-05_broker_handoff.json',
}


def hydrate(raw=None):
    raw = raw if raw is not None else os.environ.get('SCANNER_PRIVATE_CONFIG', '')
    if not raw:
        raise RuntimeError('PRIVATE_CONFIG_NOT_CONFIGURED')
    bundle = json.loads(raw)
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
        self.repo = os.environ.get('SCANNER_STATE_REPOSITORY', '')
        self.token = os.environ.get('SCANNER_STATE_TOKEN', '')
        if not self.repo or not self.token:
            raise RuntimeError('PRIVATE_STATE_NOT_CONFIGURED')
        self.sha = None
        self.path = 'migration_runtime/public_scanner_' + mode + '_state.json'
        self.metadata = self.request('')
        if self.metadata.get('private') is not True:
            raise RuntimeError('STATE_REPOSITORY_MUST_BE_PRIVATE')

    def request(self, suffix, data=None):
        req = urllib.request.Request('https://api.github.com/repos/' + self.repo + suffix,
            data=json.dumps(data).encode() if data is not None else None,
            method='PUT' if data is not None else 'GET',
            headers={'Authorization': 'Bearer ' + self.token,
                     'Accept': 'application/vnd.github+json',
                     'X-GitHub-Api-Version': '2022-11-28'})
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                return json.load(res)
        except Exception:
            # Never echo authenticated URLs, payloads or provider exception strings.
            raise RuntimeError('PRIVATE_STATE_REQUEST_FAILED') from None

    def load(self):
        # A missing state must be initialized explicitly; never silently reset deduplication.
        record = self.request('/contents/' + self.path)
        self.sha = record['sha']
        state = json.loads(base64.b64decode(record['content']))
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
