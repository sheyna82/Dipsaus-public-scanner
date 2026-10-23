# Local exchange-calendars dependency inventory — 2026-10-23

Read-only inspection of preinstalled packages in an isolated assistant execution environment. No installation or changes to DIPSAUS live scanner.

- exchange-calendars: 4.13.1
- numpy: 2.3.5
- pandas: installed (version should be separately recorded before any lock)
- pyluach: 2.3.0
- toolz: 1.1.0
- tzdata: 2026.2
- korean-lunar-calendar: 0.3.1

The upstream package requires numpy>=1.26.4, pandas>=1.5.0, pyluach>=2.3.0, toolz>=1.0.0, tzdata>=2025.2, korean_lunar_calendar>=0.3.1. This is not a resolved, reproducible dependency lock: some package metadata contain optional extra dependencies, and transitive runtime requirements still need to be captured.

**Security and licensing status:** upstream exchange_calendars license is Apache-2.0; installed package metadata alone are insufficient to verify all licenses or security advisories. No CVE scan, hash-pinned lock, SBOM, or attested 4.13.2 installation has yet been completed.

**Audit finding:** expected-session checking formerly limited its completeness flag to the first/last available price bar, allowing missing edge sessions to be overlooked. Fixed by separate full-supplied-calendar coverage flags and regression tests.

**Next gate:** use a dedicated offline environment with a hash-pinned 4.13.2 wheel and all transitive dependencies; produce SBOM, vulnerability scan report, official exchange holiday cross-check and a reproducible session export. Do not copy this machine's environment into production.
