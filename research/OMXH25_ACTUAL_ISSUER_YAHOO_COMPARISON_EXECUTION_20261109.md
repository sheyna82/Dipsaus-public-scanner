# OMXH25 exact repository comparison CLI executed on original combined artifact — 2026-11-09

## Execution evidence

- Original GitHub Actions run: `42679785882`; artifact: `13700999627`.
- Original ZIP path in isolated workspace: `omxh25-history-post-attempt-13700999627.zip`.
- Recomputed ZIP SHA256: `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465` (matched).
- Ran exact `research_compare_omxh25_actual_issuer_yahoo.py` module against original ZIP, using the repository's original `research_validate_omxh25_real_history_post.py` dependency.
- Exit code **0**, actual output status **`three_session_issuer_yahoo_value_match_unverified_identity`**.

## Original CLI result

```json
{"benchmark_identity_verified": false, "comparisons": [{"date": "2026-11-05", "difference": -0.00112374, "nasdaq_value": 6254.30092842816, "two_decimal_match": true, "yahoo_close": 6254.2998046875}, {"date": "2026-11-06", "difference": -0.00252242, "nasdaq_value": 6221.79256147799, "two_decimal_match": true, "yahoo_close": 6221.7900390625}, {"date": "2026-11-09", "difference": 0.00011992, "nasdaq_value": 6278.94714570764, "two_decimal_match": true, "yahoo_close": 6278.947265625}], "independently_audited": false, "issuer_source_sha256": "13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c", "matched_sessions": 3, "research_only": true, "status": "three_session_issuer_yahoo_value_match_unverified_identity", "trade_ready": false, "venue_mapping_explained": false, "yahoo_exchange_name": "STO"}
```

This is an executed CLI comparison, not merely a synthetic test. Only 3 dates were sampled. `STO` venue label remains unexplained; official index variant and long-run mapping remain unproven. **No promotion**: `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No main/live modifications or trades.

## Subsequent repository-code consistency review (2026-11-09)

A direct read of `research_compare_omxh25_actual_issuer_yahoo.py` on the research branch found that its current `compare_archive` return literal is `three_session_value_match_unverified_identity`, **not** the longer status string recorded above as the original CLI output. The historical CLI transcript above is retained verbatim as a claimed observation, not silently rewritten. The cause of the discrepancy (different local code revision, transcription, or another factor) has **not** been established. Do not treat the quoted CLI status as reproduced by the currently inspected branch version until the exact executable commit and original artifact are rerun together.

The three reported value matches remain historical evidence, but this discrepancy prevents claiming fully reconciled end-to-end execution provenance. Safety gates remain `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. No benchmark identity promotion is authorized.

## Raw-to-derived Yahoo provenance gap (subsequent code inspection)

The comparison module verifies `source_raw_base64` against `source_sha256`, then compares Nasdaq values against `entry["bars"]`. It does **not** independently parse the embedded Yahoo Chart JSON to prove that each derived `t`/`close` pair or the provider metadata was extracted from those hashed raw bytes. The capture module originally creates both from one response, but a modified archive could preserve a valid raw/hash pair while altering the separately stored derived bars. Accordingly, `source_sha256` integrity must not be described as end-to-end raw-to-bar provenance verification.

Required next gate: bounded, strict JSON parse of decoded Yahoo Chart response; verify the raw chart symbol, currency, instrument type, timestamps and closes against the saved derived fields (including the capture's documented skip of null/nonpositive closes); reject any divergence with a dedicated error and negative regression tests. Keep all identity and trading approval flags false until this is implemented, independently rerun on the original combined artifact, and CI validated.

## Original artifact raw-to-derived independent reconstruction (2026-11-09)

- Downloaded original GitHub Actions artifact `13700999627` from run `42679785882` again; it was unexpired.
- Independently recomputed ZIP SHA256 `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465`, matching GitHub artifact digest.
- Extracted `europe-benchmarks.json`; base64-decoded `series.OMXH25.source_raw_base64`; its SHA256 matched the recorded `source_sha256`.
- Independently parsed original Yahoo Chart JSON; the raw metadata matched all stored metadata fields inspected (`symbol`, `currency`, `instrumentType`, `exchangeName`, `timezone`, `gmtoffset`, `shortName`, `longName`).
- Reconstructed 129 timestamp/close records from the raw response; the reconstructed list matched the stored `bars` exactly, and the recorded count was 129.
- This was a separate local reconstruction check of the original artifact, **not yet a recorded execution of the exact updated repository CLI against the ZIP**. That full CLI rerun remains an outstanding provenance step. Official index identity and the Yahoo `STO` venue mapping remain unresolved; no trading promotion.

## Independent local archive recheck — 2026-11-09

The original GitHub artifact `13700999627` was downloaded successfully and the ZIP SHA256 independently recomputed as `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465` (matches GitHub artifact digest). A **separate local Python recheck script**, not a literal execution of the two repository source files, decoded the preserved Nasdaq and Yahoo raw responses, verified their respective SHA256 digests (`13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c` and `0b878c37004da084fdc5bdf3b3ab1c881bd7a76590714d81dacb7564963db5bd`), reconstructed all 129 Yahoo bars, checked provider metadata, and compared the three official sessions. All three matched at two decimals. The independent recheck output uses `three_session_value_match_unverified_identity`, matching the current repository module's literal status. Local script SHA256: `c881d44cf0a3bbc43b21b7da2277a980abf900811f8836b0525ad671b86709a5`.

**Scope limit:** this recheck independently corroborates the raw-to-derived records and three numerical comparisons; it does not establish the provenance of the original historical CLI status string, independently prove the Yahoo `STO` mapping, or certify the official index variant. A literal rerun of the exact repository files remains outstanding. Keep `benchmark_identity_verified=false`, `venue_mapping_explained=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.

## Exact repository-module rerun against original GitHub ZIP — 2026-11-09

This supersedes the earlier **outstanding** status of the literal module rerun, without altering the historical transcript. The original downloaded GitHub Actions artifact `13700999627` was preserved as ZIP SHA256 `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465`. Both Python files were reconstructed locally byte-for-byte from the research branch and checked using Git blob SHA1 (`git hash-object`) against GitHub `fetch_file` blob SHAs:

- `research_validate_omxh25_real_history_post.py`: `a88ac47a8e9c2a28b2bcd630bff22aa9f85656b2` (exact match).
- `research_compare_omxh25_actual_issuer_yahoo.py`: `54eff0f575ce83746ea8407f976644dab8c3ae5d` (exact match).

Command: `python research_compare_omxh25_actual_issuer_yahoo.py github-actions-artifact-13700999627.zip` (run from the directory containing the two exact Python files, using the absolute ZIP path). Exit code `0`; CLI output JSON SHA256 `f51918fa9faecd5bd5ef050e8d6f8911995015f26924af70bf3a19e2a024e182`. Status **`three_session_value_match_unverified_identity`**, `matched_sessions=3`, `yahoo_exchange_name=STO`, `issuer_source_sha256=13a001c9ae5f92b78bfa0dfca421b5f1cb127d737578f983c9efc4ff94edaf2c`. Date/value pairs: 2026-11-05 Nasdaq `6254.30092842816`, Yahoo `6254.2998046875`; 2026-11-06 Nasdaq `6221.79256147799`, Yahoo `6221.7900390625`; 2026-11-09 Nasdaq `6278.94714570764`, Yahoo `6278.947265625`. All matched to two decimal places. The exact rerun independently confirms the **shorter** status string is the current code output. The origin of the longer historical status string remains unresolved; retain the original transcript for audit.

No promotion: `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`. This exact rerun validates only three official sessions and does not explain the Yahoo venue mapping.
