# Calendar audit vulnerability finding and remediation — 2026-10-23

Source: GitHub Actions run 39972316027, evidence artifact 12508873688, `calendar-vulnerabilities.json`.

The scan found exactly one reported vulnerability:
- `setuptools==79.0.1`
- `PYSEC-2026-3447`, `CVE-2026-59890`, `GHSA-h35f-9h28-mq5c`
- Advisory reports fix in `setuptools>=83.0.0`.
- The advisory concerns Unicode normalization in source-distribution exclusion rules on macOS APFS/HFS+; it is not evidence of a vulnerability in exchange-calendars' date calculations.

The isolated audit workflow now installs `setuptools==83.0.0` before `exchange_calendars==4.13.2` and `pip-audit==2.9.0`. The vulnerability scan remains fail-closed; no production dependency has been changed. This is a remediation *attempt*, not proof of success until the next CI run completes.

The same run passed Python dependency consistency checks and verified recorded real XNYS/XAMS session dates for version 4.13.2. Still missing: complete license review, wheel hash pinning, independent official holiday verification, full historical market data, and demonstrated predictive lift.
