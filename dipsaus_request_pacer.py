"""Small, dependency-free, thread-safe request pacing primitive.

Opt-in only: not connected to live scans. No secrets, tickers or responses logged.
"""
import threading
import time


class SharedRequestPacer:
    def __init__(self, min_interval_seconds=0.25, clock=None, sleeper=None):
        if min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be nonnegative")
        self.min_interval_seconds = float(min_interval_seconds)
        self.clock = clock or time.monotonic
        self.sleeper = sleeper or time.sleep
        self.lock = threading.Lock()
        self.next_allowed = None

    def wait(self):
        # Hold the lock through sleeping to prevent simultaneous starts.
        with self.lock:
            now = self.clock()
            if self.next_allowed is not None and now < self.next_allowed:
                self.sleeper(self.next_allowed - now)
                now = self.clock()
            self.next_allowed = max(now, self.next_allowed or now) + self.min_interval_seconds
