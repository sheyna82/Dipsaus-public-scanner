"""Dependency-free, thread-safe pacing for a single process.

Opt-in only. No network requests, logs, or scanner integration.
"""
import math
import threading
import time


class SharedRequestPacer:
    def __init__(self, min_interval_seconds=0.25, clock=None, sleeper=None):
        if not math.isfinite(min_interval_seconds) or min_interval_seconds < 0:
            raise ValueError("min_interval_seconds must be finite and nonnegative")
        self.min_interval_seconds = float(min_interval_seconds)
        self.clock = clock or time.monotonic
        self.sleeper = sleeper or time.sleep
        self.lock = threading.Lock()
        self.next_allowed = None

    def wait(self):
        """Reserve one request slot, with process-wide spacing."""
        with self.lock:
            now = self.clock()
            if self.next_allowed is not None and now < self.next_allowed:
                self.sleeper(self.next_allowed - now)
                now = self.clock()
            self.next_allowed = max(now, self.next_allowed if self.next_allowed is not None else now) + self.min_interval_seconds

    def defer(self, seconds):
        """Apply a shared cooldown, e.g. after a provider 429 response.

        The caller must parse and cap provider retry hints before calling.
        This method does not retry or swallow failed requests.
        """
        if not math.isfinite(seconds) or seconds < 0:
            raise ValueError("seconds must be finite and nonnegative")
        with self.lock:
            now = self.clock()
            until = now + seconds
            self.next_allowed = max(until, self.next_allowed if self.next_allowed is not None else now)
