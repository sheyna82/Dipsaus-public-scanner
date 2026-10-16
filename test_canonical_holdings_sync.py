import base64
import json
import tempfile
import unittest
from pathlib import Path

from safe_runner import sync_canonical_positions


class Store:
    def __init__(self, data):
        self.data = data

    def request(self, path):
        assert path == '/contents/config/profit_exit_watch.json'
        return {'encoding': 'base64', 'content': base64.b64encode(json.dumps(self.data).encode()).decode()}


class CanonicalHoldingsTests(unittest.TestCase):
    def test_all_positions_replace_stale_holdings(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'watch.json'
            p.write_text(json.dumps({'positions': {'SOLD': {'shares': 5}}, 'other': 'preserved'}))
            sync_canonical_positions(Store({'positions': {'FER': {'shares': 71}, 'RENK': {'shares': 50}}}), p)
            data = json.loads(p.read_text())
            self.assertEqual(set(data['positions']), {'FER', 'RENK'})
            self.assertEqual(data['other'], 'preserved')

    def test_invalid_canonical_state_never_overwrites_watch(self):
        for positions in ({}, {'FER': {'shares': 0}}, {'FER': {'shares': True}}, {'FER': {'shares': float('inf')}}):
            with self.subTest(positions=positions), tempfile.TemporaryDirectory() as d:
                p = Path(d) / 'watch.json'
                p.write_text('{"positions":{"FER":{"shares":71}}}')
                original = p.read_text()
                with self.assertRaisesRegex(RuntimeError, 'PRIVATE_CONFIG_SYNC_INVALID'):
                    sync_canonical_positions(Store({'positions': positions}), p)
                self.assertEqual(p.read_text(), original)


if __name__ == '__main__':
    unittest.main()
