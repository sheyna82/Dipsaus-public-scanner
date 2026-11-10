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

## Dynamic-import audit extension CI verified — 2026-11-09

Research-only AST inventory now flags literal legacy imports through `importlib.import_module` and `__import__`, plus computed imports through those two call patterns as `unknown_dynamic_import`; gate treats all `kind=dynamic_import` as unreviewed, regardless of allowlist. Commits `a37bf81b2c85c83562493195f617a70102cf1847`, `d5a2bdcc58f70b144a40dab08f1890cc779d2876`, `60b8c62c749ba495ce4d60b1e43db63c5bda02f8`, `5d0fc2a05b4a2348386230cf33aa0caea9fdbcfc`. GitHub Actions run `42685513439`, job `129391142221`: **26 tests OK**. All seven workflows for commit `5d0fc2a05b4a2348386230cf33aa0caea9fdbcfc` completed `success`. Audit found 31 historical test calls, 2 controlled delegations, 0 unreviewed calls. **Limitations:** this is static pattern matching; aliasing importlib, `getattr`, `exec`, reassigned imports, reflection and runtime-generated calls are not exhaustively covered. No real source admission or licensing proven; trust registry intentionally empty.

## Reflection and dynamic-code static gate — verified 2026-11-09

Commit `0537ad4c8c54e1c077d5bbcc2d3ae427a6ac9150` extends the AST inventory to `getattr(legacy_module, method)` and `exec`/`eval` for computed code or literal code mentioning legacy module names. These flagged categories are never allowlisted. GitHub Actions run `42685749359`, job `129391978168`, confirmed **31 tests OK**, including five new regressions. Audit classification: 31 historical test calls, 2 controlled delegations, 0 unknown/flagged calls. At the time of documentation, six of seven workflows completed successfully; AMD capture workflow remained in progress. This static audit is not an exhaustive runtime/data-flow analysis; computed aliasing and external code remain outside proof. Trusted benchmark registry remains empty and historical calculations unchanged.

## Simple assigned function alias audit — CI verified 2026-11-09

Commit `adae6979f31ba9ee185ff53c4a7802f6380bf82c` adds AST detection for straightforward aliases of directly imported historical EU functions and imported module attributes, with two regression tests. GitHub Actions run `42685916349`, job `129392568272`: **33 tests OK**. All seven workflows for the commit finished successfully. Actual inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed calls. Scope limitation: AST-wide alias collection is not execution-order-aware and is not a full data-flow analysis; alias shadowing/rebinding, nested scopes, closures, reflection and dynamically generated code require additional validation. Historical calculations unchanged; no benchmark source admitted.

## Ambiguous legacy alias rebinding — CI verified 2026-11-09

Commit `11bd9bb1097090fd90848d6fcd38969cb004942d` adds a fail-closed `ambiguous_alias` finding for assignment rebinding of a tracked historical function alias to a different or unknown value, plus two regression tests. GitHub Actions run `42686322838`, job `129394007781`: **35 tests OK**; all seven workflows succeeded. Inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Important limitation: this is conservative AST-wide name matching, not scope-aware, order-aware or control-flow-sensitive; additional false positives or missed complex paths remain possible. Historical research calculations and trusted-source registry unchanged.

## Local scope shadowing ambiguity — CI verified 2026-11-09

Commit `c819ff2933473e8eb666615d9f0021e9a7d28c8b` adds a conservative `ambiguous_scope` AST finding for local parameters and assignment targets that shadow imported legacy names, and three regression tests. GitHub Actions run `42686564065`, job `129394838848`: **38 tests OK**. All seven workflows for the code commit completed `success`. Inventory remains 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limitations: this is not a complete scope-aware dataflow or runtime call graph; conservative ambiguity detection can overreport and nested scopes/control-flow need independent analysis. No benchmark admission, historical calculation changes, main/live updates or trading orders.

## Nested lexical scope shadowing refinement — CI verified 2026-11-09

Commit `9545dc75024511a408973d91561c7fcf99973068` limits local-shadowing discovery to the current lexical function scope and flags nested function definitions that shadow a legacy imported name. Two new regression tests confirm inner assignments are not incorrectly attributed to the outer function and nested function definitions are flagged. GitHub Actions run `42686763302`, job `129395543650`: **40 tests OK**. All seven workflows completed successfully. Inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limitations: this still does not implement complete Python lexical resolution, scope-bound imports, nonlocal/global semantics, execution order or control-flow tracking. No source rights admission or historical calculation changes.

## Global/nonlocal legacy-name redirection audit — CI verified 2026-11-09

Commit `283863a475dfcd3ec442a14a5198d84586f334ec` adds conservative AST reporting of `global` and `nonlocal` declarations involving names associated with legacy European research functions, with two regression tests. GitHub Actions run `42686950864`, job `129396190926`: **42 tests OK**. All seven workflows for this code commit completed successfully. Inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limitations: the name map is collected file-wide; this flags potential redirection, not definitive runtime resolution. Python scopes, aliases, imports and execution order remain only partially modeled. No benchmark admitted, no historical calculation changes.

## Function-local legacy imports audit — CI verified 2026-11-09

Commit `c48e56a4bda576f0d72efe794dcffc73e6686615` flags legacy module/function imports occurring within function lexical scopes (including nested scopes) as `ambiguous_scope`, preventing file-wide import-name inference from silently allowing uncertain cases. Two new regression tests passed. GitHub Actions run `42687155455`, job `129396906989`: **44 tests OK**; all seven workflows completed successfully. Inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limits: conservative detection, not complete scope binding, alias/control-flow tracking or proof of runtime target; no real benchmark admission or historical calculation changes.

## Module-level legacy alias execution-order ambiguity — CI verified 2026-11-09

Commit `3d57ec98c70d00b59274dc686acc7f07474cf2dd` introduces `ambiguous_order` findings when a legacy-associated top-level name is both called and reassigned to an unrelated expression. The gate rejects this uncertainty; two regression tests added. GitHub Actions run `42687521396`, job `129398213717`: **46 tests OK**; all seven workflows completed successfully. Inventory remains 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limits: this flags ambiguous timelines; it does not infer precise runtime state or full control flow. No benchmark source admitted and no historical calculation or live changes.

## Supplemental ordered-alias diagnostic — CI verified 2026-11-09

Commit `a0dbec1cc08b60cf0ac255118f2efd8f546c23c4` adds `research_europe_ordered_alias_diagnostic.py` and three isolated regression tests, executed by the benchmark-source-admission offline workflow. The diagnostic distinguishes simple top-level legacy calls before and after rebinding, follows direct module-function aliases and marks unproven calls without claiming legacy provenance. GitHub Actions run `42687753737`, job `129399032914`: **49 tests OK**, all seven workflows successful. Existing inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. This diagnostic is **not integrated into the enforcing gate** and cannot grant exemptions; nested scopes, branches, loops and dynamic execution remain out of scope. No source admitted or live changes.

## Ordered-alias branch/loop uncertainty — CI verified 2026-11-09

Commit `ffa7290313c68c42d70c0e0fc8a7ca03f22836d3` conservatively invalidates prior top-level alias evidence on compound control-flow statements (`if`, loops, `try`, `with`, `match`) and emits `uncertain_control_flow`. Three regression tests cover branch uncertainty, loop uncertainty and restoration of confidence after explicit re-import. GitHub Actions run `42687977476`, job `129399820919`: **52 tests OK**, all seven workflows successful. Existing inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. The diagnostic remains supplemental and is not used to relax the fail-closed gate. This is not full path-sensitive dataflow analysis and does not inspect branch-internal call targets. No historical calculation, benchmark admission, main or live change.

## Nested calls inside compound control flow — CI verified 2026-11-09

Commit `a9c38ac5f7f30b383c5e47b3442ef6e3d5c52f59` adds a conservative `uncertain_nested_call` inventory for calls syntactically within compound control flow, while excluding calls inside nested function/class/lambda definitions and avoiding any runtime-target claim. Three regression tests cover branches, loops and nested definitions. GitHub Actions run `42688187825`, job `129400563304`: **55 tests OK**; all seven workflows completed successfully. Legacy inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. This supplemental diagnostic is not an enforcing gate, and cannot resolve nested calls to verified runtime targets or grant source admission. No changes to historical calculation logic, main or live trading.

## Expression-level nested call inventory — CI verified 2026-11-09

Commit `96ec0d5ff574851737a70f2f5e80596604a9bd44` adds supplemental `uncertain_expression_call` findings for calls within assignment right-hand sides and nested top-level call expressions. Three regression tests cover assignment RHS, nested arguments and a legacy outer call with nested argument. GitHub Actions run `42688396978`, job `129401301144`: **58 tests OK**; all seven workflows completed successfully. Existing legacy inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. The diagnostic does not yet cover all Python expression contexts, is not used by the enforcing gate, and grants no benchmark source admission. No changes to historical calculations, main or live scanner.

## Deferred return/condition call inventory — CI verified 2026-11-09

Commit `56af23072e15a287c3069af6c3c8a3a3c87c35f6` adds supplemental syntactic inventory of calls in return expressions and function-level `if`/`while` conditions, classified `uncertain_deferred_expression_call`, plus calls in module-level `assert` conditions as `uncertain_expression_call`. Three regression tests added. GitHub Actions run `42688968461`, job `129403295721`: **61 tests OK**; all seven workflows successful. Legacy gate inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Supplemental diagnostic is not a runtime execution proof or a replacement for the enforcing gate. No benchmark admission or changes to historical calculations, main or live scanner.

## Definition-time versus deferred function calls — CI verified 2026-11-09

Commit `5c52b81c700977aba44829d1696d76d6120043c1` extends the supplemental ordered-alias diagnostic to inventory decorator, default argument and annotation calls separately as `uncertain_definition_time_call`; calls in return/condition expressions inside the function body remain `uncertain_deferred_expression_call`. Three regressions cover default values, decorator calls and the immediate/deferred distinction. Annotation evaluation semantics vary with Python version and future imports; classification does not assert actual runtime execution. GitHub Actions run `42689820223`, job `129406287815`: **64 tests OK**; all seven workflows successful. Legacy gate inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. Supplemental diagnostic is not an enforcing gate. Remaining gaps include arbitrary expression statements, class bodies, nested scopes and comprehensive Python execution-order modeling. No benchmark admission, historical calculation change, main change or live scanner change.

## Function-body versus class-body calls — CI verified 2026-11-09

Commit `2328184214a06bc22df25b278606d8d8596d20a6` adds supplemental `uncertain_deferred_body_call` inventory for direct expression statements within ordinary function bodies and `uncertain_class_body_call` inventory for direct class-body expressions and assignment RHS. Three regression tests distinguish deferred function calls from class creation-time calls and avoid treating a method body as an immediate class-body call. GitHub Actions run `42690149280`, job `129407438752`: **67 tests OK**; all seven workflows completed successfully. Legacy inventory: 31 historical test calls, 2 controlled delegations, 0 unreviewed. This is syntactic coverage, not comprehensive scope- or execution-sensitive analysis; nested class bodies, method decorators/defaults, and arbitrary statement forms remain unproven. Supplemental diagnostic is not part of the enforcing gate. No changes to historical calculations, main or live scanner.

## Method definition and nested class expressions — CI verified 2026-11-09

Commit `8448687286596226368925157308151c986f6b36` adds supplemental class-creation-time inventory for direct method decorators/defaults and nested class decorators/bases/keywords. Three regression tests passed: method decorator, method default, nested class base/decorator. GitHub Actions run `42690336454`, job `129408093728`: **70 tests OK**, all seven workflows successful. Legacy gate inventory remains 31 historical test calls, 2 controlled delegations, 0 unreviewed. Limits: no complete traversal of nested class bodies, annotations and all arbitrary statement forms; syntactic inventory does not establish runtime execution or source admission. Enforcing gate unchanged; no main/live scanner changes.


## Ordered alias diagnostic: nested class-body CI verification (2026-11-09)

- Verified exact code commit: `b2d7799882675d74569df7d2dbd43e358e0e2c09` on `research/integrated-evidence-20261106`.
- All seven associated pull-request workflow runs completed with conclusion `success` (GitHub commit-associated workflow query).
- Benchmark source admission offline tests: run `42690608599`, job `129409032522`; actual job log reports `Ran 73 tests in 0.012s` and `OK`.
- EU relative strength offline gate tests: run `42690608572`, offline-gates job `129409032125`, log reports `Ran 145 tests in 0.193s` and `OK` (a separate test suite, not an alternative count for the 73 admission tests).
- Legacy gate job output independently enumerates 31 `historical_test`, 2 `controlled_delegation`, and 0 unknown direct calls; unchanged from prior verified inventory.
- New nested class-body traversal and three associated regression tests are included in the verified 73-test suite. CI success verifies tested behavior only, not complete Python scope semantics.
- The ordered alias diagnostic remains supplemental, non-admitting research evidence; the fail-closed legacy gate and empty trusted source receipt registry must not be weakened. No benchmark-source identity approval or trade-ready status follows from this CI result.
- Next priority: inspect real scope/definition-time gaps and possible duplicate call findings before changing the diagnostic again; add code only for a demonstrated defect and preserve isolation from main/live/trading.


## Nested function scope boundary CI verification (2026-11-09)

- Code commit `6dee1a067437122de8fcb23d88e399a3eee0b97e`; regression test commit `a9cccc226e8baadb3e4150d729be1fef01d6e3af`.
- The supplemental ordered-alias diagnostic no longer traverses nested function, lambda, or class definitions when inventorying return/condition/assert calls belonging to an enclosing function. Three targeted tests cover nested synchronous functions, asynchronous functions, and nested class methods.
- Verified exact test-commit GitHub Actions workflow run `42691328068`, job `129411501179`: `Ran 76 tests in 0.015s`, `OK`; the three new scope tests individually show `ok` in the job log.
- All seven commit-associated workflows completed with `success`: `42691328738`, `42691328415`, `42691328728`, `42691328440`, `42691328068`, `42691328787`, `42691328689`.
- The legacy gate remains green: 31 `historical_test`, 2 `controlled_delegation`, zero unreviewed direct legacy calls, as independently counted from the source-admission job log.
- Scope analysis is deliberately incomplete: this patch prevents incorrect outer-function attribution; it does not inventory nested-function bodies as separate independently modeled scopes. No promotion to an admission gate, source verification, or trade-ready status is justified.
- GitHub Actions logged a Node.js 20 deprecation warning for pinned checkout/setup-python actions; workflows succeeded. Review this maintenance warning separately without changing security-sensitive action pins casually.


## Top-level class header expression inventory: CI verification (2026-11-09)

- Code commit `3983ce2f19df36d24316566b6eafed145aff1afa`; regression-test commit `03c82d0a8196e29b44baeebd9dc4f3357ce96939`.
- Supplemental AST diagnostic now inventories calls in top-level class decorators, base expressions and class keyword values, matching the existing conservative treatment of nested class headers. It does not claim execution or legacy target identity.
- GitHub Actions source-admission workflow run `42691502041`, job `129412100022`: `Ran 78 tests in 0.020s`, `OK`; both new top-level class-header tests explicitly passed.
- All seven commit-associated workflows completed with `success`: `42691501659`, `42691501742`, `42691502058`, `42691502024`, `42691501822`, `42691502041`, `42691501753`.
- Legacy audit log still contains 31 `historical_test`, 2 `controlled_delegation`, and no unknown direct legacy calls. The enforced gate succeeded.
- The diagnostic remains supplemental, not an admission gate; no trusted source receipts, live scanner, main branch or trading logic were changed. Further AST expansion requires a concrete evidence gap and should not be treated as strategy validation.


## Augmented assignment alias invalidation: CI verification (2026-11-09)

- Code commit `7608181f79c4d3e148499f03a3aa6732b5f75e3e`; regression-test commit `474e9a5470d1f8c7701b42fa0fbb405a1e0d4b60`.
- Supplemental ordered-alias diagnosis now invalidates a proven top-level alias after name-target augmented assignment, inventories RHS calls as uncertain, and conservatively clears the alias map for non-name augmented targets. This avoids falsely carrying a proof through `+=` without claiming a resolved runtime identity.
- Exact-commit source-admission GitHub Actions run `42691683490`, job `129412738009`: `Ran 80 tests in 0.017s`, `OK`; both augmented-assignment regression tests passed.
- Seven of seven workflows completed successfully: `42691683763`, `42691683718`, `42691683828`, `42691683448`, `42691683490`, `42691683785`, `42691683352`.
- Enforced legacy gate succeeded; job-log audit recorded 31 `historical_test`, 2 `controlled_delegation`, and zero unknown direct legacy calls.
- This is conservative supplemental AST evidence, not an admission-gate promotion, independent market-source verification, or a live trading change. `main` and the live scanner remain untouched.


## Import rebinding and wildcard alias invalidation: CI verification (2026-11-09)

- Code commit `23bf1c38be35014597bb0b85eca50cf18b74af47`; regression-test commit `5ae21cbc7db415ca34200f2fc7cbaf3c72162a2c`.
- Supplemental ordered-alias diagnosis now updates bound names for all ordinary imports and from-imports, not only recognized legacy imports. Unknown wildcard imports invalidate the known alias state; an explicit later recognized legacy import can re-establish a proof. This prevents stale alias identities after import shadowing.
- Exact-commit source-admission GitHub Actions run `42691879606`, job `129413418183`: `Ran 84 tests in 0.018s`, `OK`; all four new import-rebinding regressions passed.
- Seven of seven workflows completed successfully: `42691879736`, `42691880148`, `42691879714`, `42691880304`, `42691879606`, `42691880064`, `42691879809`.
- Legacy audit log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls; the enforced gate succeeded.
- This diagnostic remains supplemental and conservative. No admission promotion, trusted source receipt, live scanner or trading logic changes; no merge to `main`.


## Function-definition alias shadowing: CI verification (2026-11-09)

- Code commit `0c8250cfd2d80b1556bc04649a87dcf0ea6fb919`; regression-test commit `ae08fc801b1700b622bdd875e981c16a635166c3`.
- Supplemental ordered-alias diagnostic now invalidates an earlier proven top-level legacy alias when a synchronous or asynchronous function definition binds the same name. A later explicit recognized legacy import can restore proof. Decorator/default/annotation expression inventory remains conservative.
- Exact-commit GitHub Actions source-admission run `42692026415`, job `129413935426`: `Ran 87 tests in 0.013s`, `OK`; all three new function-definition regressions individually passed.
- All seven workflows completed with `success`: `42692026430`, `42692026332`, `42692026119`, `42692026344`, `42692026415`, `42692026395`, `42692026092`.
- Enforced legacy gate succeeded; job-log audit contains 31 `historical_test`, 2 `controlled_delegation`, and zero unknown direct legacy calls.
- This remains supplemental AST evidence only. No source admission promotion, trusted receipt, live scanner or trading logic modification, and no merge to `main`.


## Class-definition alias shadowing: CI verification (2026-11-09)

- Code commit `a3872d9eca67eee67022468d619da2db5f93b434`; regression-test commit `dc04c2fa59b924ee97adf2a2ea52649164d24212`.
- Supplemental ordered-alias diagnostic now invalidates a previously proven top-level legacy alias when a class definition binds the same name, including decorated classes. A later explicit recognized legacy import can restore proof.
- Exact-commit GitHub Actions source-admission run `42692416810`, job `129415305436`: `Ran 90 tests in 0.024s`, `OK`; all three new class-shadowing regressions passed individually.
- All seven workflows completed successfully: `42692416736`, `42692416720`, `42692417205`, `42692417146`, `42692417192`, `42692416810`, `42692417130`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- This is supplemental, conservative AST evidence only. No trusted source receipt, benchmark admission promotion, live scanner/trading changes, or merge to `main`.


## Tuple/list unpacking alias invalidation: CI verification (2026-11-09)

- Code commit `2694fe2d683bb18464d3977e3723014cc2138f42`; regression-test commit `31c9672090ffe5d9a408306938953d1afd3e2b01`.
- Supplemental ordered-alias diagnosis now invalidates proven names bound by tuple/list unpacking (including nested and chained assignment targets), without inferring the identity of unpacked values.
- Exact-commit GitHub Actions source-admission run `42693076674`, job `129417641896`: `Ran 93 tests in 0.019s`, `OK`; all three unpacking regression tests passed individually.
- All seven workflows completed successfully: `42693076908`, `42693076897`, `42693076674`, `42693077321`, `42693076550`, `42693077041`, `42693076634`.
- Enforced legacy gate succeeded; audit log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no source admission promotion, trusted receipt, live scanner/trading logic modification or merge to `main`.


## Walrus assignment in top-level call expressions: CI verification (2026-11-09)

- Code commit `645285858a3df1bf46e8f7f4330fa712fac82772`; regression-test commit `07761a20abd43d5c8422971ddd7a74d5ef1a96d7`.
- Supplemental ordered-alias diagnostic conservatively invalidates names bound by `ast.NamedExpr` within top-level call expression statements, including nested walrus assignments. It does not claim runtime identity or evaluation-order proof.
- Exact-commit source-admission GitHub Actions run `42693254180`, job `129418271888`: `Ran 95 tests in 0.022s`, `OK`; both new walrus regressions passed individually.
- All seven workflows completed successfully: `42693254208`, `42693254174`, `42693254180`, `42693254135`, `42693254338`, `42693254149`, `42693254246`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no source admission promotion, trusted receipt, live scanner/trading logic modification, or merge to `main`.


## Walrus bindings in non-call top-level expressions: CI verification (2026-11-09)

- Code commit `019a775c54922a46c56caeb6993f2bda2c007d8c`; regression-test commit `bc783da7597072ada1334e86900e8384cb76d70f`.
- Supplemental ordered-alias diagnostic now invalidates names bound by `ast.NamedExpr` in non-call top-level expression statements, including conditional expressions and f-strings. Calls nested in such expressions are inventoried as uncertain, without claiming execution or runtime identity.
- Exact-commit source-admission GitHub Actions run `42693395853`, job `129418777221`: `Ran 98 tests in 0.022s`, `OK`; all three new regressions passed individually.
- All seven workflows completed successfully: `42693395903`, `42693395850`, `42693396311`, `42693396081`, `42693396260`, `42693395853`, `42693396184`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Walrus bindings in assignment RHS: CI verification (2026-11-09)

- Code commit `bd95df59ea5c20def4bac85f429acc58efaf998d`; regression-test commit `f8e72541cf0ba9d5e6cf33ac523c553791d8bacd`.
- Supplemental ordered-alias diagnostic invalidates names bound by `ast.NamedExpr` in ordinary assignment RHS expressions, including nested walrus expressions. No execution or runtime identity is inferred.
- Exact-commit source-admission GitHub Actions run `42693557304`, job `129419342728`: `Ran 101 tests in 0.151s`, `OK`; all three new regressions passed individually.
- All seven workflows completed successfully: `42693557748`, `42693557566`, `42693557814`, `42693557625`, `42693557525`, `42693557304`, `42693557480`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Top-level `del` alias invalidation: CI verification (2026-11-09)

- Code commit `70d9297a4c96565cdf36dcc92161d257d7e46006`; regression-test commit `c807d0357f2b4093f02e83e773d601dcf6f5e53b`.
- Supplemental ordered-alias diagnostic invalidates aliases explicitly deleted by top-level `del` and conservatively clears proof for attribute/subscript deletion with possible side effects. Deletion of an unrelated plain name preserves other aliases.
- Exact-commit source-admission GitHub Actions run `42693817360`, job `129420229184`: `Ran 104 tests in 0.026s`, `OK`; all three new regressions passed individually.
- All seven workflows completed successfully: `42693817669`, `42693817647`, `42693817843`, `42693817399`, `42693817697`, `42693817360`, `42693817415`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Side-effecting assignment targets: CI verification (2026-11-09)

- Code commit `3194e059f3cc0e1fa117926b4724cc5db80227c0`; regression-test commit `938d2e7100af1eddb3fe0810b8a589f417c30b83`.
- Supplemental ordered-alias diagnostic conservatively clears alias proof for attribute/subscript assignment targets, including such targets nested in unpacking, because property or item assignment may execute arbitrary code.
- Exact-commit source-admission GitHub Actions run `42694056923`, job `129421069575`: `Ran 107 tests in 0.030s`, `OK`; all three new regressions passed individually.
- All seven workflows completed successfully: `42694056498`, `42694056434`, `42694056427`, `42694056429`, `42694056391`, `42694056923`, `42694056857`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Walrus bindings in augmented-assignment RHS: CI verification (2026-11-09)

- Code commit `c0b888efbae643082a8dc2dafcb75f585a04c10d`; regression-test commit `b134fa27e12894c7008696025f4a7b87ebb739a7`.
- Supplemental ordered-alias diagnostic invalidates other aliases rebound by `ast.NamedExpr` inside an augmented-assignment RHS, including nested walrus expressions; unrelated plain-name augmented assignments preserve independent alias evidence.
- Exact-commit source-admission GitHub Actions run `42694229282`, job `129421661855`: `Ran 110 tests in 0.027s`, `OK`; all three new regressions passed individually.
- All seven workflows completed successfully: `42694228862`, `42694228848`, `42694228988`, `42694229078`, `42694229390`, `42694229282`, `42694228841`.
- Enforced legacy gate succeeded; log inventory: 31 `historical_test`, 2 `controlled_delegation`, zero unknown direct legacy calls.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Isolated AMD historical workflow YAML repair: CI verification (2026-11-09)

- Research-branch-only workflow configuration fix commit `36352abed5f9702c52128f704f1872f5f3404b63` repaired a malformed literal `\\n` joining the offline AMD contract-test step `name` and `run` fields in `.github/workflows/research-amd-historical-isolated.yml`.
- Previously failing push workflow `42694216299` had no jobs; this is evidence of a pre-job workflow issue, not a proven failed AMD test. The YAML repair was limited to the affected step structure.
- Exact-commit isolated AMD historical workflow `42695465222`, job `129426016101`: `Ran 5 tests in 0.005s`, `OK`; job and workflow concluded `success`.
- All nine exact-commit GitHub Actions runs completed successfully: `42695464804`, `42695465222`, `42695464846`, `42695464814`, `42695465036`, `42695465078`, `42695464772`, `42695465294`, `42695454135`.
- Runner logged Node.js 20 deprecation/forced Node.js 24 warning for pinned GitHub Actions; follow up as maintenance, not a test failure.
- No benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Definition-time walrus alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `c59b1f544e82f0d0a5476d9e04f2d416a6d8153d`; regression-test commit `412194a9a2618147a6fe1826025be252ec1fe31e`.
- Function-definition decorators and defaults may execute walrus bindings at definition time; the diagnostic now conservatively invalidates the affected prior alias proof. An unrelated function definition retains independent alias evidence.
- Exact-commit source-admission run `42695611873`, job `129426529273`: `Ran 116 tests in 0.018s`, `OK`; the three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42695625602`, `42695626137`, `42695625622`, `42695626089`, `42695625661`, `42695625677`, `42695625591`, `42695625866`, `42695611873`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Class-header walrus alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `358657dec8e205c96395672aaac3d109a58a9358`; regression-test commit `376f646635c77bb9566b3be714c90ed1ae32404e`.
- Top-level class decorators, bases and keyword expressions may execute walrus bindings during class creation; the diagnostic now conservatively invalidates the affected earlier alias proofs. An unrelated class definition preserves independent alias evidence.
- Exact-commit source-admission run `42695761113`, job `129427062314`: `Ran 120 tests in 0.015s`, `OK`; all four new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42695774907`, `42695773509`, `42695773422`, `42695773378`, `42695773225`, `42695773232`, `42695773197`, `42695773321`, `42695761113`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Assert-expression walrus alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `0711f4e23bfaa98b00c2d9b3f595d1ca7ca35f62`; regression-test commit `c713b7914bf17e8e688e9ac0474326f5f2d0e0f1`.
- `assert` condition and optional message expressions may execute walrus bindings; the diagnostic now conservatively invalidates affected prior alias proof and inventories calls in both expressions as uncertain. Unrelated assertions preserve independent alias evidence.
- Exact-commit source-admission run `42695949025`, job `129427709690`: `Ran 124 tests in 0.032s`, `OK`; all four new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42695961607`, `42695962311`, `42695961722`, `42695961544`, `42695961578`, `42695961472`, `42695961965`, `42695961981`, `42695949025`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Relative versus absolute legacy import alias proof: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `d69cc554ec762b9b22de58f39ad0439dafb5bef6`; regression-test commit `c0d9d5cdd8357fc11036a9eaa3c651257a22640e`.
- Relative `from .module import name` and `from ..module import name` cannot prove identity with the absolute legacy module. The diagnostic now requires `ImportFrom.level == 0` for proven legacy function aliases; an absolute import retains its prior classification.
- Exact-commit source-admission run `42696133378`, job `129428339779`: `Ran 127 tests in 0.015s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42696140446`, `42696140863`, `42696140177`, `42696140113`, `42696140282`, `42696140197`, `42696140627`, `42696140145`, `42696133378`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Class-body global declaration alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `158627a5d3fe3679c3cb394fca83d7149a0cf4b8`; regression-test commit `9ee5922e6cb2500f27dc8b7b055df20a5f44870c`.
- A `global` declaration inside a class body, including nested classes, can make subsequent assignments affect the module namespace. The supplemental diagnostic now conservatively invalidates declared names; ordinary class-local assignments preserve independent module alias proof.
- Exact-commit source-admission run `42696333006`, job `129429038586`: `Ran 130 tests in 0.019s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42696348891`, `42696349134`, `42696349099`, `42696348842`, `42696349170`, `42696348745`, `42696349290`, `42696349129`, `42696333006`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Class-body nested global declaration alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `c18d1195c03bebc5d5495485840e10ceef958d25`; regression-test commit `c82dfa999f461d64b324eea8e26325cfce3c7bb8`.
- Class-body `global` declarations nested inside control-flow suites can affect module alias bindings. The diagnostic conservatively invalidates these names while avoiding deferred method/function scopes; nested classes are inspected separately.
- Exact-commit source-admission run `42696513154`, job `129429679693`: `Ran 133 tests in 0.025s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42696522846`, `42696522813`, `42696522881`, `42696522474`, `42696522492`, `42696522071`, `42696522496`, `42696522273`, `42696513154`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Class-local walrus scope preservation: regression-only CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic regression-only commit `d85e7c567f7f3cce6b30fffdeb76f097c095ed8e`; no production or diagnostic code change was needed.
- Three tests confirm that class-local walrus assignment, nested class base-expression walrus, and method default-expression walrus do not incorrectly invalidate an independent module-level alias proof in the examined cases.
- Exact-commit source-admission run `42696718006`, job `129430412627`: `Ran 136 tests in 0.030s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42696731867`, `42696731733`, `42696731481`, `42696731303`, `42696731710`, `42696731371`, `42696731662`, `42696731329`, `42696718006`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Direct exec dynamic alias invalidation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `9e7ad54459e5b646a95d9370f374ec3676167781`; regression-test commit `ba365331d0c814b4bcdca4e9f9355fdb1a73630b`.
- A direct expression-statement call to `exec(...)` conservatively clears earlier module alias proofs, because dynamic code may rebind them. The new tests cover direct exec, exec with explicit namespace, and an unrelated call that preserves alias proof. This does not assert complete coverage of all dynamic-execution forms.
- Exact-commit source-admission run `42696914827`, job `129431099241`: `Ran 139 tests in 0.017s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42696921619`, `42696921782`, `42696921735`, `42696921458`, `42696921707`, `42696922026`, `42696922125`, `42696921796`, `42696914827`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in assignment and assert expressions: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `46558e8c5a2b05d31cdb52f1fda4e57a7ef9b002`; regression-test commit `5009999a2a7273cdbef891441fbae84bbe671adb`.
- Direct `exec` calls nested within assignment RHS or assert condition/message expressions conservatively invalidate earlier module alias proofs. The assert-message branch may not execute; the diagnostic intentionally remains fail-closed. Other dynamic execution contexts remain open for investigation.
- Exact-commit source-admission run `42697126866`, job `129431843623`: `Ran 142 tests in 0.019s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42697138431`, `42697138833`, `42697138604`, `42697139117`, `42697138702`, `42697138591`, `42697138348`, `42697139195`, `42697126866`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in augmented assignment RHS: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `11f40eb6f9edb5c00ca3de27e1c35566892ab956`; regression-test commit `5fa90c94686f01b68ecc6b2b5882b9cd2b8209bb`.
- A direct `exec` call nested in the RHS of an augmented assignment conservatively invalidates earlier module alias proofs. An unrelated ordinary augmented assignment retains a separate proven alias in the tested case.
- Exact-commit source-admission run `42697322530`, job `129432522090`: `Ran 143 tests in 0.032s`, `OK`; both new regression tests passed individually. The previously forecast 144-test count was incorrect; 143 is the observed log count.
- All nine exact-commit workflows completed successfully: `42697336062`, `42697336063`, `42697336250`, `42697336185`, `42697336041`, `42697335973`, `42697336297`, `42697336386`, `42697322530`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec inside non-call expression statements: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `56e2e8c77154afa77d3b0fc7f8bae34596531e15`; regression-test commit `758a46fa0f993d4075ad0eba1e33334d2add608f`.
- A direct `exec` call nested inside a non-call expression statement, including f-string or tuple expression, conservatively invalidates earlier module alias proofs. An unrelated f-string preserves an existing alias proof in the tested case. This does not establish complete coverage of all dynamic execution contexts.
- Exact-commit source-admission run `42705937882`, job `129462607747`: `Ran 146 tests in 0.031s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42705948806`, `42705949155`, `42705948880`, `42705949019`, `42705949502`, `42705949058`, `42705948830`, `42705948904`, `42705937882`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in function/class definition-time expressions: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `cc1d1c19a6985b4b7851767d340f35993d1566c1`; regression-test commit `116ce25abe988f8209f4bd41e80c40758e8ff6af`.
- Direct `exec` calls nested in function default/decorator expressions and class base/decorator expressions conservatively invalidate earlier module alias proofs. Four regression tests cover these execution-time cases. This does not establish complete coverage of dynamic rebinding or all class-body expressions.
- Exact-commit source-admission run `42706158551`, job `129463373529`: `Ran 150 tests in 0.030s`, `OK`; all four new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42706169335`, `42706168727`, `42706168675`, `42706169588`, `42706168908`, `42706168644`, `42706169628`, `42706168854`, `42706158551`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec during class-body creation: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `04800a68c56b977e41391d6709c670f131278c88`; regression-test commit `453fe46f914e81ff77eb75e84d3effb1bea5766e`.
- Direct `exec` calls in class-body expression statements or assignment RHS conservatively invalidate earlier module alias proofs, including possible explicit `global` rebinding. A deferred method-body `exec` does not immediately invalidate the module alias in the tested case. This does not establish exhaustive coverage of nested class control flow or dynamic execution.
- Exact-commit source-admission run `42706329073`, job `129463965288`: `Ran 153 tests in 0.028s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42706340658`, `42706340702`, `42706340679`, `42706340288`, `42706340407`, `42706340331`, `42706340386`, `42706340577`, `42706329073`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in class-body assert and augmented assignment: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `015fb125966b7d1b3c135310566c8f49df1be3d1`; regression-test commit `bf99f511df8a4901eeaed0e8048e2f83be2103ca`.
- Direct `exec` nested in class-body assert conditions/messages and augmented assignment RHS conservatively invalidates prior module alias proofs; an ordinary assert preserves proof in the tested control. This does not establish exhaustive coverage of nested class control flow or dynamic execution.
- Exact-commit source-admission run `42706519754`, job `129464636977`: `Ran 156 tests in 0.032s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42706531820`, `42706531592`, `42706531604`, `42706531655`, `42706531578`, `42706531821`, `42706531502`, `42706531599`, `42706519754`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in nested class control flow: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `00ee5b0dfaac2d8d41d1de25c4e6b09e89faec32`; regression-test commit `b9ea36c8f8f1d51538580697b625f7799d860ea5`.
- Class-body scanner now visits statements in nested if/for/while/try/with/match suites and checks selected control-flow header expressions for direct nested `exec`, conservatively invalidating prior module alias proofs. Four regression tests cover class if body, for body, try body, and if header. Remaining gaps include exception handler headers, match guards, and other dynamically evaluated expressions; no completeness claim.
- Exact-commit source-admission run `42709509602`, job `129474997751`: `Ran 160 tests in 0.018s`, `OK`; all four new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42709521300`, `42709521364`, `42709521360`, `42709521697`, `42709521714`, `42709521784`, `42709521637`, `42709521290`, `42709509602`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Exec in class match guards and exception handler expressions: CI verification (2026-11-09)

- Supplemental ordered-alias diagnostic code commit `1b2a31419ba14bcc9d156be5cc0298d385498d97`; regression-test commit `e294c6ebcb7b6b945520d5bb3acc8db90320df60`.
- Direct `exec` nested in class-body match case guards and exception handler type expressions conservatively invalidates prior module alias proofs. Three regression tests cover both cases and a non-exec match guard control. These cases do not establish exhaustive handling of all class-body expressions or all dynamic rebinding mechanisms.
- Exact-commit source-admission run `42709695543`, job `129475643473`: `Ran 163 tests in 0.027s`, `OK`; all three new regression tests passed individually.
- All nine exact-commit workflows completed successfully: `42709707592`, `42709708090`, `42709707695`, `42709707555`, `42709707848`, `42709708121`, `42709707668`, `42709707523`, `42709695543`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Supplemental AST evidence only; no benchmark source admission promotion, trusted receipt, live scanner/trading logic change, or merge to `main`.


## Architecture review: ordered alias diagnostic execution-context risks (2026-11-09)

Scope: static review of `research_europe_ordered_alias_diagnostic.py` after 163-test verified milestone. **This is a risk inventory, not a code change, CI verification, or claim of runtime exploitability.**

1. **Duplicated execution scanning (high maintenance risk):** direct `exec` detection appears in multiple statement branches; each new syntax form requires a separate manual update. Proposal: introduce a single execution-context-aware expression walker with explicit policies for module statements, class-creation expressions, and deferred function/lambda bodies. Retain conservative invalidation and preserve existing classifications unless independently justified.
2. **Class-body coverage is incomplete (potential false proof):** the current nested-suite traversal covers selected `if/for/while/try/with/match` headers and bodies, but does not explicitly model every expression or all Python syntax forms. In particular `ast.TryStar` (`except*`) is absent, and class-body `ast.AnnAssign` annotation expressions are not in the explicit class expression list. Confirm actual evaluation semantics before treating a candidate as executable.
3. **Execution-time vs deferred scopes (false-positive risk):** generic `ast.walk` over a definition-time expression can descend into nested lambda/comprehension or other deferred bodies. The new walker should distinguish code executed during class/function definition from code merely constructed then, with positive and negative regression controls.
4. **Dynamic namespace mutation beyond direct `exec` (potential false proof):** alias state can be changed via indirect calls, namespace dictionaries, imported helpers or `eval` of dynamically constructed code. Do not assert that matching direct `exec` is exhaustive; determine a bounded, auditable policy for unknown calls rather than treating them as proven safe.
5. **Proof model and test strategy:** retain the fail-closed enforced legacy gate as authority. Use small executable Python semantics fixtures, mutation/property-oriented test matrices and exact-commit CI evidence to validate a future refactor. No change to the live scanner, order execution, source admission, or benchmark trust receipts.

Recommended next small step: add a focused, regression-only failing-case inventory for `except*` and class annotation execution semantics, then design the centralized walker **before** adding more one-off branches. No merge of draft PR #65.


## Known execution-context gaps captured as expected failures (2026-11-09)

- Regression-only commit `96269b9a46045f3aac8791ec400a90da14921ab0`; no diagnostic implementation changes in this round.
- Added two deliberately marked `@unittest.expectedFailure` cases: direct `exec` in a class-body `except*` suite and direct `exec` in an evaluated class annotation expression. Both currently retain a stale legacy alias proof in the supplemental ordered-alias diagnostic. A plain class annotation control passes.
- Exact-commit source-admission run `42709922767`, job `129476429959`: `Ran 166 tests in 0.033s`, `OK (expected failures=2)`; both gap cases reported `expected failure` and the control reported `ok`. Green CI does **not** mean these gaps are fixed.
- All nine exact-commit workflows completed successfully: `42709931965`, `42709932155`, `42709932153`, `42709932154`, `42709932022`, `42709931996`, `42709931781`, `42709931841`, `42709922767`.
- Enforced legacy audit inventory in job log: 31 `historical_test`, 2 `controlled_delegation`, zero unknown classifications.
- Next: design an execution-context-aware centralized expression visitor, use the two known failing fixtures as acceptance tests, and only remove `expectedFailure` markers after observing actual passing tests. No merge of draft PR #65, live change, source admission promotion, or trusted receipt.


## Centralized class-creation expression scanning: exact-commit CI verification (2026-11-09)

- Research-only code commit `1e9abc71fbf8d1b68a93404e751667b8492da1b7` introduced `_scan_class_creation_expressions`, `ast.TryStar` traversal and class annotation inspection. Test commit `cabf3ccd03a1d9877c6756d4b1ba47b79d7278ad` removed the two known `expectedFailure` markers. The first run exposed a missing colon at the class control-flow condition (seven successes and two source-admission failures); do not represent that commit as verified.
- Syntax repair `ad327f4608d709efa112cd48ef1a350eb69784a5` restored parsing but exposed three class-local walrus regressions in 166 executed tests. Intermediate correction `ae4a30b16b660dc380d12119e142101e3261c954` fixed those while exposing three module-header walrus regressions. Neither intermediate commit passed the complete suite.
- Final verified code commit: `b7164410cc18f789396fb43fd8708806dc1306f5`. The class-creation expression scanner now distinguishes module-scope class header bindings from expressions evaluated within class bodies via an explicit `module_scope` argument. The existing regression tests were not weakened.
- Exact-commit source-admission run `42710689388`, job `129479097814`: `Ran 166 tests in 0.023s`, `OK`. Both `test_known_gap_class_trystar_exec_invalidates_alias` and `test_known_gap_class_annotation_exec_invalidates_alias` individually reported `ok`; no expected failures were reported.
- All nine exact-commit workflows completed successfully: `42710689068` (SPY), `42710689388` and `42710677987` (source admission), `42710689043` (OMXH25), `42710688824` (AMD historical capture), `42710689289` (EU relative strength), `42710688787` (research evidence integrity), `42710689221` (European recovery), `42710688776` (AMD offline contracts).
- Enforced legacy gate output in source-admission job: 31 `historical_test`, 2 `controlled_delegation`, zero `unknown` classifications. This is a bounded static diagnostic and gate result, **not** proof of exhaustive Python runtime alias analysis.
- Scope remains research-only. No merge to `main`, production scanner or order logic change, trusted receipt promotion, or live trading action. Follow-up: independently inspect evaluation-context semantics and add focused controls before any further visitor refactor.


## Immediately invoked class lambda: execution-context regression verified (2026-11-10)

- Research-only regression inventory commit `e238c12527d8a84f6f6e09b53ffa465daa07ce9a` added two cases: direct lambda invocation during class creation containing `exec` with a global alias reassignment, and an uninvoked lambda control. Exact-commit source-admission run `42710997555`, job `129480177663`: `Ran 168 tests in 0.026s`, `OK (expected failures=1)`; the direct invocation was an expected failure and the uninvoked control passed.
- Code commit `06b91687db35aa567acbcf8980929e7f44eff734` scans the body of a directly invoked lambda in the class-creation expression walker. Test commit `9197911a4bf473d8a20f2d9b013be183dd1bf03e` removed the expected-failure marker so the regression must pass.
- Exact-commit source-admission run `42711142890`, job `129480675792`: `Ran 168 tests in 0.033s`, `OK`; both the direct-invocation regression and uninvoked-lambda control individually reported `ok`. No expected failures were reported.
- All nine exact-commit workflow runs succeeded: `42711143108` (evidence integrity), `42711142956` (AMD historical), `42711143016` (European recovery), `42711142826` (EU relative strength), `42711142890` and `42711131550` (source admission), `42711143180` (AMD contracts), `42711142960` (SPY), `42711142897` (OMXH25).
- Enforced legacy gate: 31 `historical_test`, 2 `controlled_delegation`, zero `unknown` classifications.
- This is a bounded AST fix, **not** a claim of exhaustive Python execution modeling. Nested lambda invocations, dynamic indirection, and conditional execution remain subjects for separate research. No `main` merge, live scanner/order change, source-admission promotion, or trusted receipt promotion.


## Ordered class-local lambda bindings: exact-commit CI verification (2026-11-10)

- Regression inventory commit `67b0c55e48a2d7c9e4095ffb3c75e21142784ee2` added a known expected-failure case for a class-local lambda assigned to a name and invoked later during class creation, plus a non-invocation control. Exact-commit source-admission run `42772947026`, job `129684738505`: `Ran 170 tests in 0.026s`, `OK (expected failures=1)`; both cases were individually observed.
- Research-only code commit `8627e382de6b1d64b1a24f008a0bb27a07cd4176` introduced an ordered, per-class `local_lambdas` registry for simple name-bound lambdas and conservative invalidation on supported rebinding forms. Test commit `f306da77fdfae41c1ba6664e26073623d9cecddb` removed the expected-failure marker and added controls for overwrite-before-call and nested-class name isolation.
- Exact-commit source-admission run `42773440541`, job `129686338288`: `Ran 172 tests in 0.017s`, `OK`; the previously failing invocation case and both additional controls individually reported `ok`. No expected failures.
- All nine exact-commit workflows completed successfully: `42773448886` (AMD historical), `42773448758` (EU relative strength), `42773448821` and `42773440541` (source admission), `42773448713` (European recovery), `42773449075` (OMXH25), `42773449293` (research evidence integrity), `42773448754` (SPY), `42773448809` (AMD contracts).
- Enforced legacy audit: 31 `historical_test`, 2 `controlled_delegation`, zero `unknown` classifications.
- Scope limitation: the class-local registry handles only simple ordered assignments and selected rebinding forms. It is not a complete model of dynamic Python name resolution, branches, exception flow, indirect calls or runtime alias mutation. No promotion to source-admission authority, no merge to `main`, no live scanner or trading-order change.


## Conditional class lambda rebinding: verified conservative regression (2026-11-10)

- Regression inventory commit `75f5c8071448f627c51d3613a9fef49ce53b00e3` added a branch-dependent lambda overwrite case as `expectedFailure` and an unconditional overwrite control. Exact-commit source-admission run `42773575479`, job `129686769135`: `Ran 174 tests in 0.020s`, `OK (expected failures=1)`. The branch-dependent case was an expected failure; unconditional control passed.
- Research-only code commit `5203de44ff82d6fdb3843687d19dd80ef6e9007d` makes the class-body walker fail closed for conditional assignment/deletion nodes when flattening compound suites; test commit `cfc2c61fa177926192bb47b60e7007526646c394` removes the expected-failure marker.
- Exact-commit source-admission run `42773648060`, job `129687002749`: `Ran 174 tests in 0.019s`, `OK`; both conditional and unconditional overwrite cases individually `ok`, no expected failures.
- All nine exact-commit workflow runs completed successfully: `42773654446` (EU relative strength), `42773654684` and `42773648060` (source admission), `42773654401` (SPY), `42773654306` (European recovery), `42773654615` (OMXH25), `42773654651` (evidence integrity), `42773654460` (AMD historical), `42773654499` (AMD contracts).
- Enforced legacy gate remains 31 `historical_test`, 2 `controlled_delegation`, zero `unknown` classifications.
- Scope limitation: flattening nested control-flow suites is not path-sensitive execution modeling; other conditional expression side effects, exceptional exits, name indirection, and dynamic Python semantics remain outside proven coverage. This evidence does not authorize production promotion or a merge. `main`, live scanner and trading orders unchanged.


## Nested conditional and exceptional class lambda paths: verified existing protection (2026-11-10)

- Test inventory commit `59d62e19c6e2c351515da1d8c8886fbd946b7f7d` introduced nested conditional rebinding and `try`/`except` rebinding cases as `expectedFailure`. Exact-commit source-admission run `42773760404`, job `129687372091`, showed **two unexpected successes** and therefore failed: both cases were already correctly classified by the existing conservative implementation. This was a test expectation error, not evidence of a code regression.
- Test-only correction commit `ed2503bdc05691bbddb049450bbbeee472fb9385` removed the two `expectedFailure` decorators. No analysis-code change was needed.
- Exact-commit source-admission run `42773818315`, job `129687556324`: `Ran 176 tests in 0.019s`, `OK`, both new cases individually `ok`, no expected failures.
- All nine exact-commit workflows succeeded: `42773818276` (evidence integrity), `42773818315` and `42773811803` (source admission), `42773818312` (OMXH25), `42773818223` (EU relative strength), `42773818569` (European recovery), `42773818268` (AMD historical), `42773818533` (SPY), `42773818283` (AMD contracts).
- Legacy gate unchanged: 31 `historical_test`, 2 `controlled_delegation`, zero `unknown` classifications. Earlier documentation commit `45ab865016b3b15173684b817d0b0acc33c9a9c1` also completed nine successful workflows.
- Evidence is restricted to these tested AST cases. It does not prove full path sensitivity, exception ordering, or Python dynamic name resolution. No merge, live-scanner change, or trading action.


## Nested exec call-argument evaluation: proven follow-up alias invalidation (2026-11-10)

- Initial regression inventory `d5c95fed8d085b899252eac03e315d7f27fcd18e` incorrectly expected the outer call itself to lose proof. Python evaluates a callable before its arguments, so that expectation was revised before any code change.
- Corrected regression inventory `ed9e8ede97c79aecfc7f4cece36eca08043b339d` distinguishes `compare(exec(...))` (outer callable already resolved) from a *subsequent* `compare()` (name resolved again after potential global rebinding). Source-admission run `42774109955`, job `129688480136`, recorded 179 tests with exactly one expected failure, and nine exact-commit workflows succeeded.
- Minimal implementation `5a41f3e21c59078e76c8925bc2e37083b4e0dbc5` invalidates alias state **after** classifying the outer call if nested direct `exec` is present. Mandatory regression-test commit `f79c0080ffe81d44a0ca39f37d1047669f1d79b9` removes the expected-failure marker.
- Source-admission run `42774183645`, job `129688717123`: `Ran 179 tests in 0.037s`, `OK`, both semantic-order regression tests individually `ok`, no expected failures. All nine workflows for `f79c0080ffe81d44a0ca39f37d1047669f1d79b9` succeeded: `42774183906`, `42774183991`, `42774183963`, `42774183660`, `42774183584`, `42774183645`, `42774183737`, `42774183642`, `42774177551`.
- Legacy gate unchanged: 31 `historical_test`, 2 `controlled_delegation`, 0 `unknown`. This is bounded evidence for nested direct `exec` in a module-level call expression; it is not a claim of complete Python dynamic execution coverage.
- Research branch only; PR #65 remains draft. No main merge, live-scanner modification, or trading action.


## Evaluated annotation exec: verified conservative alias invalidation (2026-11-10)

- Regression inventory commit `78ab0985738e0bc8976bfb870de65b628c9efaa1`: direct `exec` within an annotated assignment's annotation expression was not invalidating previously proven module aliases. Exact-commit source admission run `42774288137`, job `129689052324`: 181 tests, exactly one expected failure; ordinary `int` annotation control passed. All nine workflows succeeded.
- Minimal code fix `fc4d2032f6b7847a953809c25f4be7ea4f6e7811` clears module alias proofs on direct `exec` encountered in an `AnnAssign` annotation expression. Test commit `a6d2ab54f019ac243b4177df4461f92e45e4ce2e` promotes regression to mandatory.
- Source admission run `42774361175`, job `129689292443`: `Ran 181 tests in 0.028s`, `OK`, both annotation cases individually `ok`, no expected failures. All nine workflows for the exact commit succeeded: `42774367657`, `42774367705`, `42774367618`, `42774367341`, `42774367274`, `42774367289`, `42774367319`, `42774367266`, `42774361175`.
- Legacy audit unchanged: 31 `historical_test`, 2 `controlled_delegation`, 0 `unknown`. Conservative handling intentionally does not prove runtime evaluation of postponed annotations; Python version and future annotations can defer expression execution.
- Research branch only; PR #65 draft, no merge to main, no live-scanner change, no trading action.


## Class method annotations: verified conservative alias invalidation (2026-11-10)

- Regression inventory commit `1321e150d078a7514f18aa64558a7c5d466a3a7c` identified a missing check for `exec` inside class method parameter annotations. Source admission run `42774486648`, job `129689684458`: 183 tests, exactly one expected failure; the ordinary `int` annotation control passed. The preceding dossier commit `c8f960218b87ae258617b5b5f138c66103b9dc0f` independently passed all nine workflows.
- Minimal source fix `556efeddeb252299a17da6b7595bd5206c6f75af` includes parameter and return annotations in class method definition-time expression scanning, preserving existing decorator/default scanning. Mandatory regression test commit `a518fdd7256792c35987b81187f7438f226b9aad` removes the expected-failure marker.
- Exact-commit source admission run `42774541402`, job `129689866708`: `Ran 183 tests in 0.020s`, `OK`; both annotation tests `ok`, no expected failures. All nine workflows succeeded: `42774549445`, `42774549474`, `42774549281`, `42774549423`, `42774549415`, `42774549813`, `42774549311`, `42774549294`, `42774541402`.
- Legacy audit unchanged: 31 `historical_test`, 2 `controlled_delegation`, 0 `unknown`. Static scanning remains intentionally conservative: Python versions and postponed annotation evaluation can affect runtime timing, and this analysis does not claim to establish actual execution of annotation expressions.
- Research branch only; PR #65 remains draft; no merge to main, live-scanner change or trading action.


## Nested class method return annotations: existing protection verified (2026-11-10)

- Regression test commit `6933e1def8b2c3debbe90482f736e400dc582e5a` added positive and negative controls for nested class method return annotations: direct `exec` must invalidate the previously proven imported alias, while an ordinary `int` annotation must preserve it.
- Exact-commit source admission run `42774706593`, job `129690386207`: `Ran 185 tests in 0.035s`, `OK`, both new tests individually `ok`, no expected failures. Legacy audit unchanged: 31 `historical_test`, 2 `controlled_delegation`, 0 `unknown`.
- All nine workflows succeeded for this test commit: `42774712143`, `42774712470`, `42774712018`, `42774712377`, `42774712311`, `42774712145`, `42774712280`, `42774712030`, `42774706593`.
- Existing conservative class-creation scanning already handles the tested nested return-annotation cases. No source fix required. This is static syntactic assurance, not proof of runtime execution of postponed annotations.
- Previous documentation commit `0833ed9b8edc3da6e004f5de6bc48a39560d81a5` also passed all nine workflows.
- Research branch only; PR #65 draft, no main merge, live-scanner change or trading action.
