"""Bridge scheduler delays with bounded, serial PRE-ALERT checks."""
import os
import subprocess
import sys
import time


def run_checks(scan, *, checks=6, interval=300, clock=time.monotonic, wait=time.sleep):
    """Start checks at five-minute intervals; never overlap or retry a failure."""
    for index in range(checks):
        started = clock()
        scan()
        print(f"PRE-ALERT check {index + 1}/{checks} completed.", flush=True)
        if index + 1 < checks:
            delay = max(0, started + interval - clock())
            if delay:
                wait(delay)


def main():
    checks = 6 if os.environ.get("GITHUB_EVENT_NAME") == "schedule" else 1
    run_checks(
        lambda: subprocess.run(
            [sys.executable, "safe_runner.py", "prealert", *sys.argv[1:]],
            check=True,
        ),
        checks=checks,
    )


if __name__ == "__main__":
    main()
