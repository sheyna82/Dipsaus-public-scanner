#!/usr/bin/env python3
"""Run market-wide fast recovery discovery first, then rotating deep discovery."""
import os, subprocess, sys
n=int(os.environ.get("US_BATCH","0")); batch=n % 21
env=os.environ.copy(); env["US_BATCH"]=str(batch)
print("US fast momentum/recovery discovery",flush=True)
# Run this first: it is the time-sensitive lane intended to catch COHR-like moves early.
rc=subprocess.call([sys.executable,"us_momentum_recovery_discovery.py"],env=env)
if rc: raise SystemExit(rc)
print(f"US PRE-ALERT rotating deep discovery batch {batch}/20",flush=True)
rc=subprocess.call([sys.executable,"us_recovery_pilot.py"],env=env)
raise SystemExit(rc)

