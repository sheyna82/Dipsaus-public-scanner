# exchange_calendars integration due diligence — 2026-10-23

Upstream: https://github.com/gerrymanoim/exchange_calendars
Inspected actual upstream default-branch pyproject.toml, LICENSE, and exchange_calendars/__init__.py using GitHub repository access.

**License:** pyproject declares Apache-2.0; LICENSE contains Apache 2.0 text; package module has Apache-2.0 copyright header. No code copied.

**Python support:** pyproject requires Python >=3.10,<4. Dependencies declared (unpinned ranges): numpy>=1.26.4, pandas>=1.5.0, pyluach>=2.3.0, toolz>=1.0.0, tzdata>=2025.2, korean_lunar_calendar>=0.3.1. This is a nontrivial supply-chain footprint. Transitive dependencies, vulnerabilities and exact release tags have not been audited.

**Integration status:** offline calendar-export adapter and expected-session audit accept externally supplied dates, but do not run upstream software. Fixture dates for XNYS/XAMS are illustrative and not independently verified. No claims of correct holiday schedules.

**Next acceptance gates:**
1. Pin and review a specific published release, not upstream master.
2. Resolve all transitive dependencies in isolated offline research environment; review licenses, hashes and security advisories.
3. Generate calendar sessions for XNYS and XAMS from pinned release and record exchange, package version, date range, SHA256 of serialized export and generation command.
4. Compare known closures, exceptional holidays, early closures and timezone handling against official exchange schedules; test delisted and suspended instruments separately (an absent daily bar may be legitimate).
5. Only after independent verification permit calendar_provenance_verified=True, and only if generated data match the recorded digest. Never imply calendar correctness from metadata alone.
6. Keep live scanner unchanged; no automatic trading or alert activation.

Current outcome: **license preliminarily suitable; installation and empirical calendar verification pending.**
