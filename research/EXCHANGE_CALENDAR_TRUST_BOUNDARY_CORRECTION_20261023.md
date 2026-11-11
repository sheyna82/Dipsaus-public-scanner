# Security review update — calendar export trust boundaries (2026-10-23)

The export's `source_sha256` is **not a package/source-code hash**. The current exporter hashes only the canonical JSON array of trading-session dates. It detects accidental changes to session data but **does not authenticate the publisher, package release, upstream source code, or official exchange schedule**. The key name is misleading; future refactoring should rename it to `session_dates_sha256` with backward compatibility. A malicious author could change both sessions and checksum.

Local environment inventory was read through Python package metadata: exchange-calendars 4.13.1, numpy 2.3.5, pyluach 2.3.0, toolz 1.1.0, tzdata 2026.2, korean-lunar-calendar 0.3.1. The pandas version was not captured in this check. This is **not** a locked or audited 4.13.2 dependency graph. Package metadata for numpy includes bundled native libraries and separate license notices; checking only top-level SPDX fields is insufficient.

Risk: missing leading/trailing sessions may reflect a genuine short listing history, delisting, or suspended trading, not necessarily broken data. The audit must distinguish data completeness from asset listing eligibility and vendor coverage.

Release acceptance remains blocked until: verified pinned wheel hash, full resolved transitive SBOM, license/NOTICE review, vulnerability scan against exact versions, official exchange holiday/exception cross-check, and independent chronological market-data validation.

The local exporter enforces 4.13.2; the read-only adapter intentionally also accepts historical 4.13.1 recorded regression fixtures. Neither is production-approved.
