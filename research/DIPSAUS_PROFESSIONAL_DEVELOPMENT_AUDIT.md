# DIPSAUS Professional Development Audit
Status: permanent research workflow; research branch only.
Date adopted: 2026-10-29.

## Objective
Build a reliable, evidence-led, professional-grade *manual* recovery-swing decision-support system, not a replica of a broker terminal. Target holding periods generally 5–15 trading sessions, up to six positions, typical EUR 3,500 tranches. Optimize **out-of-sample net portfolio outcomes**, capital efficiency, drawdown, and execution realism; never promise profitability.

## Mandatory recurring loop
1. **Inventory before development:** inspect current branch, existing modules, tests, workflows, artifacts and prior rejected experiments. Record each capability as IMPLEMENTED / PARTIAL / SPECIFIED / MISSING / REJECTED, with file paths, evidence and last verified commit. Do not confuse documentation or successful unit tests with proven trading performance.
2. **Professional capability comparison:** review relevant concepts from IBKR TWS/Risk Navigator, Bloomberg, Trade Ideas, TrendSpider, QuantConnect and comparable institutional tools. Compare *decision quality and controls*, not superficial feature count. Record why each feature matters for this strategy, availability, data dependencies, costs and licensing. No unlicensed copying of proprietary code or datasets.
3. **Gap and priority assessment:** rank missing capabilities by expected decision benefit, implementation cost, data integrity, maintenance burden, execution feasibility and risk. Prefer connecting existing modules to writing duplicates. Reject features without a measurable hypothesis.
4. **Point-in-time integrity:** verify exchange calendars/timezones, source availability timestamps, survivorship and delisting, corporate actions, stale quotes, earnings/event timestamps, data provenance, licensing, FX and transaction-cost assumptions. Unknown inputs must remain unknown, not be filled with fabricated estimates.
5. **Candidate-to-portfolio decision chain:** trace discovery -> evidence -> risk/event review -> realistic entry and spread/slippage -> position capacity/sector concentration -> scenario and downside exposure -> holding-duration/capital-lockup -> manual decision. Distinguish descriptive history from calibrated prospective forecasts. Produce a transparent blocker list.
6. **Prospective shadow evaluation:** preregister and freeze strategy version, universe, signal timestamp, ranking, eligibility, simulated fills/exits, cost assumptions, evaluation windows and baselines before observing outcomes. Preserve tamper-evident signal and outcome records. Do not call a draft protocol active; verify operational retention and timestamps first.
7. **Independent testing:** compare against simple 5/10/15-session baselines, market benchmarks and random/equal-weight alternatives. Use chronological walk-forward and purged overlapping labels where applicable, account for multiple testing, regime/quarter instability, liquidity, MAE, net return, drawdown, turnover, capital occupancy and opportunity cost. Require meaningful out-of-sample improvement, not in-sample uplift.
8. **Automated safety and quality:** offline regression, data-contract checks, deterministic reproducibility, schema validation, provenance, CI checks and failure-closed evidence gates. Audit the complete signal-to-decision integration, not only isolated modules.
9. **Decision register:** for every proposed feature record: existing implementation, professional reference, gap, hypothesis, success/failure criteria, test set, results, risks, verdict (ADOPT / REWORK / REJECT / DEFER), affected paths and commit. Revisit previously tested features only with a specific new hypothesis or data.
10. **Report clearly:** distinguish VERIFIED CODE, VERIFIED TEST, HISTORICAL RESEARCH, PROSPECTIVE EVIDENCE, SPECIFICATION and NOT VERIFIED. Never imply a GitHub change, run, live data check or trading readiness without verifying it.

## Immediate audit priorities
- Establish a single evidence-linked capability inventory and professional feature-gap matrix, reusing `research/external_scanner_component_register.md`.
- Check end-to-end integration of `research/candidate_entry_snapshot.py`, `research/candidate_decision_evidence_report.py`, `research/candidate_decision_evidence_gate.py`, and `research/candidate_portfolio_capacity.py` before creating new modules.
- Review `research/prospective_swing_protocol_v0_draft.json`: currently DRAFT_NOT_FROZEN_NOT_ACTIVE. Close its documented prerequisites before claiming a live shadow portfolio.
- Expand end-to-end CI coverage only where existing tests do not already cover the decision chain.
- Include EXE-style prolonged capital lock-up, adverse excursion, event risk and opportunity cost in acceptance tests.

## Non-negotiable guardrails
- All modifications on `research/offline-technical-risk-20261021` and PR #62 only; no merge to main without explicit approval.
- Do not change the private repository, expose private portfolio details or credentials, or introduce automatic orders.
- Manual limit-sell workflow; no default stop-loss/stop-limit orders.
- No broker connection or live trading implied by research-only code.
- A professional-looking system is not proof of profitable predictive performance.
