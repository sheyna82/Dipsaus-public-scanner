# AMD frozen-protocol evidence gate — 2026-11-09

Status: **BLOCKED — RESEARCH ONLY; NOT TRADE READY**.

## Verified evidence
- AMD historical capture: GitHub Actions run 42595156202, artifact 13663425930; workflow reports 128 daily and 1951 intraday bars.
- AMD capture offline checks and general research CI completed successfully in that run/commit sequence. These tests do not establish a valid trade.
- The existing `research/integrated_evidence_manifest.json` records prospective protocol version 1.1 and canonical JSON SHA256 `27bc6a2bf6e80b4df41faaee53726622f23f1ab495ffcd412639548d025536ee`.
- The same manifest explicitly says `protocol_embedded: false`, `validation_state: BLOCKED_PENDING_PROTOCOL_IMPORT_AND_CI`.
- `research/integrated_filter_evidence_gate.py` requires exact canonical protocol bytes, correct schema, recorded SHA256, and inactive research-only status.
- `research/dipsaus_isolated_quality_gates.py` supplies an explicit EUR bid/ask, FX, fee and slippage accounting model but does not validate any AMD-specific executable prices, FX quotes or DEGIRO fees.
- `research/integrated_recovery_decision_boundary.py` requires independently verified frozen protocol, point-in-time market data, DEGIRO eligibility, and portfolio reconciliation; it never marks trades ready.

## Unresolved before computing official DIPSAUS signal
1. Locate original protocol v1.1 JSON bytes and verify canonical SHA256, rather than reconstructing it from memory or tuning it to AMD.
2. Locate exact frozen Z-score feature definition (lookback, input price/returns, variance estimator, lagging, threshold, and timestamp) if it is part of the approved protocol; do not conflate a descriptive 20-day standardized deviation with the official signal.
3. Bind source observations and timestamp availability; independently verify relevant market and instrument identity.
4. Obtain executable bid/ask and EUR/USD quotes, verified DEGIRO tariff basis, spread/slippage scenarios and portfolio state before ex-ante net expectancy.
5. Register signal and decision before future outcomes. No retrospective performance inference from one AMD rebound.

## Explicitly prohibited
- No modifications to main or operational scanner; no broker connection or automatic orders.
- No stoploss/stoplimit assumptions.
- No invented protocol, thresholds, execution prices, fee schedules, or trade approval.

## Next isolated action
Find and import original immutable protocol bytes with the matching digest, run `integrated_filter_evidence_gate.verify` on the research branch, and only then calculate protocol-derived features from the captured AMD dataset. If source bytes cannot be located, retain BLOCKED.
