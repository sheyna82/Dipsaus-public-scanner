# US independent setup detector — historical OOS evaluation protocol (research only)

Status 2026-11-02: DESIGN CONTRACT ONLY. No historical labels or performance results have been produced.

## Preflight / no duplicate work
- Reuse `research/us_independent_setup_replay.py`, `research/us_setup_episode_evaluation.py`, `research/us_setup_snapshot_contract.py`.
- Existing GitHub pull-request regression is the current broad test gate. Do not claim the new isolated workflow runs until its own run is observed.
- Reuse existing frozen provider/snapshot infrastructure if present after inspecting provenance and coverage. Do not fabricate data or labels.

## Labeling without detector leakage
1. Freeze a historical universe and dates before looking at model outputs. Record survivorship limitations, splits, symbol mappings, corporate actions, session calendars and provider coverage.
2. Select contiguous chronological train/validation/test periods with an embargo of at least the maximum setup lookback plus the evaluation horizon. Freeze the split before tuning.
3. Independently label candidate recovery episodes using a documented human or pre-registered structural protocol **without inspecting detector output**. Include no-setup periods and ambiguous episodes. Record annotator, timestamp, raw evidence and ambiguity.
4. A label `source` string is not proof of independence. Require an independent audit record and reviewer disagreement adjudication. Do not allow detector-generated labels as ground truth.
5. Hash and freeze raw bars and labels with the existing snapshot contract; persist dataset ID, split and code SHA.

## Baselines and metrics
- Baseline A: every qualifying intraday rolling-window higher-low/reclaim (current scanner logic).
- Baseline B: a single episode per ticker until an explicit lower-low reset (simple dedupe).
- Candidate: conservative prefix-only replay detector.
- Measure one-to-one episode precision/recall, FP per ticker-day, missed-episode rate, detection delay, and counts by quarter, ticker, volatility regime and data-quality tier.
- Report confidence intervals via ticker/day clustered bootstrap; show raw numerator/denominator, not only percentages.
- If the test set has fewer than 20 independently labeled episodes in a quarter, mark that quarter INSUFFICIENT_SAMPLE; do not pool away sparse quarters.
- Treat near-duplicate overlapping bars from one episode as **one** observation for inference.

## Decision criteria, locked before running OOS
- Zero lookahead/prefix-invariance violations and zero accidental live-notification eligibility.
- On untouched test data, candidate FP per ticker-day must be lower than baseline A while recall is no worse by more than 5 percentage points; show uncertainty and raw sample sizes.
- Do not promote to live monitoring unless the lower confidence bound of FP improvement is positive and the recall noninferiority criterion is supported by uncertainty intervals.
- A detector passing episode metrics is still **not** a profitable trading strategy. Independently test entry feasibility, bid/ask, fees, EUR conversion, earnings/news, R/R, 5/10/15-day holding, capacity and opportunity cost.

## Known implementation caveats to test before historical claims
- Current `replay` uses a structural lower-low reset relative to the original anchor, not a full state machine with session-aware pivots. It may miss legitimate new higher-base setups.
- Current evaluation greedily matches detections to nearby labels; investigate whether order-dependent matching can undercount optimal one-to-one matches.
- Current snapshot hashes input content but does not certify data provenance or blinded labels.
- Current replay bar schema is low/close only; cannot infer volume, spread, news, intrabar order or executable fills.
- No historical independent labels, no OOS comparison, no benchmark superiority and no CSGP operational monitoring are verified yet.

## Safety
Research branch only. No main merge, private-repo changes, ntfy sends, broker actions, live scanner edits, or automated orders.
