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

## Outer archive strict-JSON acceptance and tamper rejection — 2026-11-09

After the strict outer-JSON parsing change (`57e92152`) and negative regression test (`cf0fbffb`), the **exact** GitHub research-branch Python modules were locally verified by Git blob SHA1: comparator `88f3d1387e05917a8b25296f28e5eca3a5e84e43`, official issuer validator `a88ac47a8e9c2a28b2bcd630bff22aa9f85656b2`. The original GitHub artifact ZIP SHA256 remained `b0aaeb32563f96f91dcc7372c96a183fb247a0cf3392c4bc94111fd23b8c0465`. Running the comparator on the original ZIP exited successfully, matched three official sessions, retained `yahoo_exchange_name=STO`, and yielded the **unchanged** CLI output SHA256 `f51918fa9faecd5bd5ef050e8d6f8911995015f26924af70bf3a19e2a024e182`.

A separate **temporary copy** of the same ZIP was deliberately modified to duplicate the `research_only` key in the outer `europe-benchmarks.json` (without modifying the original artifact). The same comparator rejected this tampered archive with `DUPLICATE_JSON_KEY`. All six GitHub Actions workflows for commit `cf0fbffb9d8874b5a5b538268457204e594161bc` completed `success`, including `EU relative strength offline gate tests` run `42683539140`.

Scope: confirms strict JSON acceptance/rejection and three-session value corroboration, **not** independent benchmark identity, Yahoo `STO` venue mapping, or trade readiness. All existing research-only/fail-closed gates remain unchanged.

## New external-source discovery: FRED Nasdaq OMXH25 daily series (2026-11-09)

Official Nasdaq methodology and index-version documents identify `OMXH25` as the Helsinki 25 **price-return** index in EUR (ISIN `FI0008900212`), distinct from gross-total-return `OMXH25GI`. Sources: https://indexes.nasdaqomx.com/docs/Index_Versions_OMXH25.pdf ; https://www.nasdaq.com/docs/2025/01/23/Finnish%20Equity%20Derivatives%20Factsheet.pdf . The St. Louis Fed FRED series `NASDAQOMXH25` explicitly attributes its daily data to **Nasdaq, Inc.**, with published table covering 2008-11-17 through 2026-11-06 at time of inspection: https://fred.stlouisfed.org/data/NASDAQOMXH25 and https://fred.stlouisfed.org/series/NASDAQOMXH25 . This is a useful **separate dissemination channel** for longer-run comparisons, but **not** an independently calculated index; Nasdaq remains its source. FRED labels this series copyrighted/pre-approval required: do not ingest/re-distribute a large historical dataset or assume unrestricted commercial/research rights without reviewing licensing and terms. No historical dataset was imported in this step.

Nasdaq's own index description confirms the Helsinki stock-price-index methodology: https://indexes.nasdaqomx.com/index/overview/omxh25 . Nasdaq derivatives documents name Nasdaq Stockholm AB as a derivatives-market legal entity, but this does **not** independently establish why Yahoo Chart metadata for `^OMXH25` reports `exchangeName=STO`. Continue to classify `venue_mapping_explained=false` and `benchmark_identity_verified=false`; no benchmark promotion or trading approval. Next investigation: verify FRED values for a bounded overlapping sample and inspect FRED/Nasdaq usage rights before any persistent data ingestion. Distinguish independent distribution from independent index calculation.

## Bounded FRED/Nasdaq/Yahoo publication-channel crosscheck — 2026-11-09

Read the public FRED series landing page https://fred.stlouisfed.org/series/NASDAQOMXH25 (observations published through 2026-11-06 at inspection) and compared the **two overlapping sessions** against the original preserved official Nasdaq EOD receipt and Yahoo Chart observations:

| Session | Official Nasdaq (2 dp) | Yahoo (2 dp) | FRED (published 2 dp) |
| --- | ---: | ---: | ---: |
| 2026-11-05 | 6254.30 | 6254.30 | 6254.30 |
| 2026-11-06 | 6221.79 | 6221.79 | 6221.79 |

FRED source page states **Source: Nasdaq, Inc.**, **Frequency: Daily**, and identifies the series as **Copyrighted: Pre-Approval Required**. This is independent **distribution-channel corroboration**, not an independent index calculation. FRED's public page did not yet display the 2026-11-09 observation at the time of inspection, so **no FRED match is claimed for 2026-11-09**. The two extra displayed observations (2026-11-04 etc.) have not been independently compared against original Yahoo raw bars in this step. No large FRED data series was fetched, saved, committed, or used for engine calculations. Licensing review remains required before data ingestion or redistribution.

This finding does not resolve Yahoo `exchangeName=STO`, independently certify index identity, or authorize trading. Maintain `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.

## Public provider/venue and data-rights review — 2026-11-09

Official Nasdaq [OMXH25 index overview](https://indexes.nasdaqomx.com/Index/Overview/OMXH25) and [Finnish Equity Derivatives factsheet](https://www.nasdaq.com/docs/2025/01/23/Finnish%20Equity%20Derivatives%20Factsheet.pdf) describe OMXH25 as the Helsinki stock **price** index in EUR (ISIN FI0008900212). This establishes the issuer's index definition, **not** the independent identity of the Yahoo historical series. Yahoo's [public `^OMXH25` instrument page](https://finance.yahoo.com/quote/%5EOMXH25/) explicitly labels it **Stockholm - Delayed Quote**. This corroborates that `STO` is not merely an artifact of the stored API JSON, but Yahoo does not explain the mapping in the checked public documentation. The [Yahoo exchanges/data-providers help page](https://help.yahoo.com/kb/finance-for-web/exchanges-data-providers-yahoo-finance-sln2310.html) describes broad index data-provider relationships, not a symbol-specific `^OMXH25` venue mapping. **Do not infer** that the underlying Helsinki index is a Stockholm-listed index or that the Yahoo code is correct/incorrect.

Rights: [FRED's ethical-use guidance](https://www.stlouisfed.org/publications/page-one-economics/2021/10/15/ethical-use-of-data-with-fred) warns that commercially redistributing copyrighted series requires copyright-holder authorization; the FRED Nasdaq index series is marked pre-approval required. [Yahoo's help](https://help.yahoo.com/kb/finance-for-web/exchanges-data-providers-yahoo-finance-sln2310.html) prohibits redistribution of Yahoo Finance data and disclaims use for trading/investing purposes. [Nasdaq legal terms](https://www.nasdaq.com/legal) restrict reuse and storage of protected data without authorization. These are source terms, not a definitive legal opinion about every research use. **No bulk FRED/Yahoo/Nasdaq dataset was imported in this review.** Prior captured raw observations remain in the historical audit artifact; assess rights before any new systematic ingestion, redistribution or commercial deployment.

Next external evidence needed: explicit provider or Nasdaq explanation of `^OMXH25`/`STO` mapping, licensed historical source terms, and independently verified longer-run index-series identity. Gates remain `venue_mapping_explained=false`, `benchmark_identity_verified=false`, `independently_audited=false`, `research_only=true`, `trade_ready=false`.

## Isolated benchmark source-admission gate: CI execution verified — 2026-11-09

New research-only files `research_benchmark_source_admission.py` (commit `8589d83b9c2f4ac04ec494e3de674de56c7fa882`) and `test_research_benchmark_source_admission.py` (commit `6cd1edfe1c5756b14cb448016a4d88221fb16347`) enforce explicit booleans for official index identity, provider-series mapping, historical-value verification and data-use rights. The separate CI workflow `.github/workflows/benchmark-source-admission-offline.yml` (commit `3fb3992e2152a79399031f22d125bf2455dec6f6`) runs the four tests directly rather than relying on the existing 145-test suite, which did not include the new test file.

**Verified GitHub Actions execution:** `Benchmark source admission offline tests`, run `42684303381`, job `129386872604`: `Ran 4 tests ... OK`. Test cases: missing/nonboolean evidence rejected; `yahoo:^OMXH25` stays blocked; trading-ready input rejected; fully documented synthetic source admitted **only** for research. All **seven** workflows attached to commit `3fb3992e2152a79399031f22d125bf2455dec6f6` completed `success` (including six existing workflows). This gate is a standalone research admission check, **not** yet integrated with all portfolio calculation paths or the live scanner. The synthetic all-true case is a contract test, not evidence of a real licensed source. OMXH25/Yahoo remains blocked due to unresolved provider mapping, insufficient long-history verification and unverified data-use rights. No merge or trading actions.

## European relative-strength admission wrapper CI verified — 2026-11-09

Research-only wrapper `research_europe_relative_strength_admitted.py` (commit `fdd641b7b3fd9ab067334fee19caf77040069ae2`) validates explicit source-admission receipts for AEX, DAX_PRICE, OMXH25, STOXX600_PRICE before delegating to unchanged `research_europe_relative_strength.compare()`. Regression tests `test_research_europe_relative_strength_admitted.py` (commit `b544d1140e8b2efb3464ed1d5762f38b48ed52d4`) cover missing receipt, unresolved Yahoo mapping, missing rights, mismatched source ID, and delegated call for fully asserted fixtures. Workflow update `28f657590cf39dd55ff11287590e57f692a8f065` runs these five tests alongside four admission-unit tests.

**Observed CI evidence:** run `42684540542`, job `129387698629`, executed exactly nine tests (`Ran 9 tests ... OK`). All seven workflows for commit `28f657590cf39dd55ff11287590e57f692a8f065` completed `success`. The existing 145-test suite remains separate.

**Critical scope caveat:** this admission wrapper currently accepts **caller-supplied boolean assertions**, not independently validated evidence receipts. A fabricated all-true receipt could pass its admission check, though the underlying calculator still has independent provenance checks. Do not describe this as cryptographic source authorization or licensed-use proof. Also, the legacy `compare()` function remains callable directly: no repository-wide enforcement has been demonstrated. Before promoting this wrapper, bind source assertions to verifiable, immutable evidence and audit every active calculation entry point. No production or live scanner changes.

## Pinned-source admission negative tests verified — 2026-11-09

New research-only wrapper requires an exact SHA256 of each source receipt to match `TRUSTED_SOURCE_RECEIPT_SHA256`, an intentionally **empty** in-code trust registry. Hash matching binds bytes, not truth, legal rights, independent audit or permission to trade. Commits: `3ba343b5a9258fe2f2c6c48ac16ccd6d9034d315` (implementation) and `444c60399133b35d780124ba01249a6f65fcc4e6` (negative tests). CI run `42684713128`, job `129388304412`, explicitly executed `Ran 11 tests ... OK`; all seven workflows for commit `444c60399133b35d780124ba01249a6f65fcc4e6` completed `success`.

**Bypass/scope audit:** `research_europe_relative_strength.compare()` is still directly callable, and the separate `research_europe_recovery_confirmation.evaluate()` relies on a caller-supplied `benchmark_identity_verified=True` flag; the new wrapper does not yet protect these historical interfaces. Existing scripts/tests may use these APIs, and no repository-wide call graph audit is complete. Do not claim global enforcement. Do not silently alter the historical functions or reclassify old research artifacts. Next step: inventory actual call sites and create a separate admission-controlled path for recovery confirmation if needed; preserve historical execution and fail closed for all new paths. No sources have been independently admitted or licensed for calculation.

## Recovery-confirmation admission wrapper: 16 tests and seven workflows green — 2026-11-09

Added isolated research-only `research_europe_recovery_confirmation_admitted.py` (commit `7f8fbf220002112cb2abc0c6b9013d0086794d9c`) and `test_research_europe_recovery_confirmation_admitted.py` (commit `c37c89d7cdb42478fff20caed5dc8a842b09ca1a`). CI workflow expanded in commit `b65e7c75f9ab47b787fd18fa543e22a0d86a62c6`. Verified GitHub Actions run `42684918488`, job `129388997891`: `Ran 16 tests ... OK`; all seven workflows for commit `b65e7c75f9ab47b787fd18fa543e22a0d86a62c6` completed `success`.

The new recovery entry point rejects source-ID mismatch, false data-rights assertion, unpinned all-true self-attestation and modified receipt before delegating to the unchanged historical `evaluate()`; positive delegation uses synthetic patched trust registry only. The production trust registry remains empty, so no real benchmark is admitted. Historical `evaluate()` and `compare()` remain directly callable; global enforcement and full call-site inventory remain **unverified**. The SHA pin is an integrity check, not independent validation of the claimed license or identity. No merge, live modification, or trade action.

## Actual offline AST legacy-call inventory — 2026-11-09

Commit `52b6b2a13b08376da7c41a4a3574a9bbddb9dc0b` added an AST-based, audit-only inventory to the benchmark-source-admission workflow. GitHub Actions run `42685105318`, job `129389659826`, verified `Ran 19 tests ... OK`. All seven workflows for the commit completed `success`. Inventory found **33 syntactic direct calls**: `research_europe_recovery_confirmation_admitted.py` 1 (intentional controlled delegation), `research_europe_relative_strength_admitted.py` 1 (intentional controlled delegation), `test_research_europe_recovery_confirmation.py` 6 (historical tests), and `test_research_europe_relative_strength.py` 25 (historical tests). No other matching calls appeared in the scanned tracked Python files. This is NOT a complete runtime call graph: dynamic imports, attribute reassignment, reflection, generated code, external consumers and non-Python entry points are not covered. No direct legacy calls were changed. The trusted receipt hash registry remains empty, and no production benchmark admitted.

## Static legacy-call enforcement: CI confirmed — 2026-11-09

Research-only CI gate added in `research_gate_europe_legacy_calls.py` and tested in `test_research_gate_europe_legacy_calls.py` (workflow commit `881ccfce379644507c1daea4cd96cf778d075855`). GitHub Actions run `42685277277`, job `129390287976`, executed **23 tests, all OK**. All seven workflows on that commit completed `success`. Actual classification of 33 AST-discovered calls: 31 `historical_test`, 2 `controlled_delegation`, 0 `unreviewed_direct_call`. CI fails if a new statically recognized direct call is not on the narrow path-and-target allowlist. Caveat: Python dynamic import/reflection, alias rebinding, other languages, generated source, external consumers and runtime control-flow remain outside this AST proof; historical tests are intentionally retained. Trusted benchmark receipt registry remains empty; this is no evidence of actual source license or benchmark admission. No production changes.
