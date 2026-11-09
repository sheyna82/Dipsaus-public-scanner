# OMXH25 portable recovery positive CI — 2026-11-09

## Verified positive execution

- Research branch: `research/integrated-evidence-20261106`, no main merge or live deployment.
- Commit `1e1762bcd28f712e15d459fb06346cea6f99733d`, GitHub Actions run `42638728533`, job `129233767892`: **SUCCESS**.
- All six workflows succeeded; EU offline gate remained at **97 tests, OK**.
- Original artifact `13680073011` SHA256 `6849ebe332ce2be42e51cd9c8537b12e755e739bc4fc4a25ec5bccfcb70fc277` checked against actual downloaded bytes.
- CI ran the checked-in `research_verify_omxh25_portable_backup.py` on a portable archive assembled **during CI from the real original artifact bytes**, and then executed its exact recovery entrypoint.
- Actual output: `portable.status=verified_portable_original_capture`; `recovery.verification.status=verified_original_bytes`; `recovery.verification.files=2`; `benchmark_identity_verified=false`; `independently_audited=false`; `research_only=true`; `trade_ready=false`.
- Derived ZIP SHA256 for this run: `0b153e88aaa8baf400ec640ab4db3333a38f575100433eee482d112e4e7cd8d6`. Derived ZIP serialization can vary; underlying pinned PDF hashes remain the authoritative checks.
- Receipt artifact `13684143233` was published and expires 2026-11-23. **At this run, the upload contained the original two receipt files, not the new portable-positive reports.** Follow-up commit `bc318b9e7ca875549b2520c094b8184850ab9434` corrects the upload paths; its CI outcome is pending at the time of writing.

## Limits

This is a positive proof for a portable archive **constructed from actual original bytes inside CI**, not a demonstration that the separately supplied downloadable ZIP has been independently retained by an external storage provider. Source artifact expiry is still 2026-11-23; no external durable backup has been confirmed. The audit of Yahoo `^OMXH25` provider exchange metadata is still incomplete. Do not promote benchmark identity or trading eligibility. No orders, main changes or live scanner changes.
