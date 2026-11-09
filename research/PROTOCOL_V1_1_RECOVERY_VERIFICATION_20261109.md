# Frozen prospective protocol v1.1 — independent recovery checkpoint (2026-11-09)

**Research-only. No operational activation.**

The original `prospective_filter_protocol_v1_1.json` was recovered from the user's existing file library, rather than reconstructed or fitted to AMD. The original bytes remain in the private user library; do not upload the protocol to the public repository without explicit authorization.

Independent local canonical JSON SHA256 check: **PASS**.

- Canonical SHA256: `27bc6a2bf6e80b4df41faaee53726622f23f1ab495ffcd412639548d025536ee`.
- Matches `research/integrated_evidence_manifest.json`.
- Schema `dipsaus.prospective_filter_evaluation.v1.1`: PASS.
- Status `RESEARCH_ONLY_VERIFIED_NOT_ACTIVATED`: PASS.
- Prospective earliest signal date `2026-11-07`: PASS.
- Exact historical source artifact ID: `13428010951`.
- Local checks used the same canonicalization and predicates as `research/integrated_filter_evidence_gate.py`. **The GitHub CI gate has not yet been rerun on the recovered file**.

Frozen AMD thresholds:
| Pattern | 20-day relative strength >= | 20-day volume ratio >= | ATR14 % <= |
|---|---:|---:|---:|
| recovery_from_prior20_low_3to15pct | -4.34385 | 0.88975 | 4.25095 |
| breakout_prior20 | 13.9879 | 1.3529 | 4.0696 |

All three features must pass, and a candidate must satisfy its pattern definition. The protocol is a research evaluation framework, not an approved trading system. A descriptive 20-day Z-score is **not** the frozen selection criterion.

Remaining:
1. Reproduce source feature definitions and time alignment from the frozen historical code without hindsight.
2. Apply to AMD observations strictly after the prospective start date, preserving data availability and full candidate registration.
3. Validate source and DEGIRO instrument identity, cost scenarios, portfolio state.
4. Obtain explicit authorization before any operational integration.

No changes to main/live scanner; no orders, no stoploss/stoplimit.
