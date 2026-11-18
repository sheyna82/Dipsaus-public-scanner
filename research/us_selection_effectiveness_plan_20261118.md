# DIPSAUS selection-effectiveness audit — 18 November 2026

Research-only. No production, live provider calls, notifications or orders.

## Hypothesis
Distinguish genuinely unattractive candidates from **unverified/pending** candidates and candidates lost before full evaluation. A high rejection fraction is not itself evidence of excessive strictness.

## Current US source-level findings
- `us_recovery_pilot.py` screens rotating batches, keeps only pre-screen matches as candidates, and has a bounded deep-dive shortlist. The early-stage denominator must include screened symbols, missing histories and candidate counts; a handoff-only report cannot measure the complete discovery funnel.
- `us_auto_prealert_handoff.py` distinguishes DEEP-RECOVERY and fast momentum candidates. Some fast candidates have `auto_promoted=True` while `structure_quality_pass=False`; this means research promotion, **not** verified structure, broker execution or a buy signal.
- `execution_blocks` include unverified bid/ask, dynamic sizing, R/R, event and portfolio checks. These are missing-evidence reasons, not proof that the price setup is unattractive.
- The offline `research/us_selection_effectiveness_audit_20261118.py` counts handoff rows, promotion, confirmed structure and block frequencies independently. It does not infer missed profits from historical hindsight.

## EU observation supplied by user (not independently reconstructed)
46 early candidates; 13 theoretical R/R >=2; 5 advanced to broker checks; zero fully trade-ready. These figures require source-level run provenance, candidate IDs, deduplication and timestamped decisions before being treated as a verified conversion funnel.

## Required next stages
1. Locate dated EU candidate decision records and extract **per-symbol, per-stage** gate outcomes, including missing data versus negative outcomes. Do not treat absence of broker evidence as a failed trade setup.
2. Quantify the gross move required to exceed EUR 150 **net** at a EUR 3500 tranche: before costs, 150/3500 = 4.2857%; with round-trip fees/spread, required gross return is higher. Account for FX, spread, sizing, target and fees per route; do not infer executable profit from historical OHLC.
3. Run offline counterfactuals with one gate varied at a time and a separate interaction analysis. Keep R/R>=2, net >=EUR150 and risk constraints unchanged for actual trade decisions.
4. For rejected symbols, use only timestamped evidence available at the decision time; evaluate subsequent outcomes separately with realistic transaction costs and survivorship controls.
5. Audit discovery coverage, batch failures, queue caps, symbol deduplication and stale routes. Report missed opportunity **rate** only when the denominator and lookahead-safe outcomes are known.
6. Produce a clear funnel: DISCOVERED / RESEARCH_PENDING / DATA_BLOCKED / TECHNICALLY_REJECTED / BROKER_PENDING / EXECUTION_VERIFIED. Never label research promotion as trade approval.

## Boundaries
Strict code freeze during NYSE hours; isolated branch only outside market hours. `trade_ready=False`, `notify=False`, `automatic_orders=False`. Do not change live scanner or draft PR #65.
