import unittest
from unittest.mock import patch

import prealert_cadence

from prealert_cadence import run_checks


class CadenceTests(unittest.TestCase):
    def simulate(self, durations, checks):
        now = [0]
        starts = []
        waits = []

        def scan():
            starts.append(now[0])
            now[0] += durations[len(starts) - 1]

        def wait(delay):
            waits.append(delay)
            now[0] += delay

        run_checks(scan, checks=checks, clock=lambda: now[0], wait=wait)
        return starts, waits

    def test_scheduled_run_only_scans_once(self):
        with patch.dict('os.environ', {'GITHUB_EVENT_NAME': 'schedule'}), patch.object(prealert_cadence, 'run_checks') as checks, patch.object(prealert_cadence.subprocess, 'run'):
            prealert_cadence.main()
            self.assertEqual(checks.call_args.kwargs['checks'], 1)

    def test_six_checks_keep_five_minute_start_interval(self):
        starts, waits = self.simulate([45] * 6, 6)
        self.assertEqual(starts, [0, 300, 600, 900, 1200, 1500])
        self.assertEqual(waits, [255] * 5)

    def test_slow_scan_never_overlaps_or_catches_up_multiple_times(self):
        starts, waits = self.simulate([650, 45, 45], 3)
        self.assertEqual(starts, [0, 650, 950])
        self.assertEqual(waits, [255])

    def test_manual_check_does_not_sleep_or_repeat(self):
        self.assertEqual(self.simulate([45], 1), ([0], []))

    def test_failed_scan_stops_without_retry_or_wait(self):
        calls = []

        def fail():
            calls.append("scan")
            raise RuntimeError("safe failure")

        with self.assertRaises(RuntimeError):
            run_checks(fail, clock=lambda: 0, wait=lambda _: calls.append("wait"))
        self.assertEqual(calls, ["scan"])
