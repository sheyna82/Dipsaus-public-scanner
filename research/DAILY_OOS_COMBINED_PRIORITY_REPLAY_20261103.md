# Combined pre-entry priority: first archived candidate-audit replay (2026-11-03)

Source: downloaded GitHub Actions artifact `candidate-feature-oos` ID `13181638404` from run `41531647491`. This is **not** the earlier artifact 13007728223; different runs give different portfolios. The ZIP contains `candidate_feature_oos.json` with 280 breakout and 639 recovery candidate-audit events.

Method: independently replayed existing `candidate_portfolio_capacity.simulate` rules (fixed €21,000 cash, €3,500 tranche, max 6 positions, same-day exit proceeds unavailable for entries) against **exact same** candidate audit event pool per pattern. Confirmed symbol_asc accepted counts and PnL exactly match archived baseline: breakout 182/+4342.38 and recovery 228/+3216.25. Pre-entry score combines existing signal-close RS20d, volume ratio and inverse ATR14, each centered on training-only threshold and clipped [-2,+2], no realized outcome in score.

| Pattern | Priority | Accepted | Rejected | Simulated realized PnL € | Occupied tranche calendar-days |
|---|---|---:|---:|---:|---:|
| Breakout | symbol_asc | 182 | 98 | +4342.38 | 2560 |
| Breakout | symbol_desc | 180 | 100 | +4794.32 | 2536 |
| Breakout | stable_hash | 178 | 102 | +2213.28 | 2507 |
| Breakout | combined score_desc | 176 | 104 | +3285.47 | 2478 |
| Recovery | symbol_asc | 228 | 411 | +3216.25 | 3194 |
| Recovery | symbol_desc | 236 | 403 | +4775.40 | 3307 |
| Recovery | stable_hash | 234 | 405 | +4481.86 | 3277 |
| Recovery | combined score_desc | 234 | 405 | +4777.37 | 3278 |

Filtered cohorts: breakout 17 accepted, 0 rejected, +809.98 in all four priorities; recovery 78 accepted, 4 rejected, +1645.49 in all four priorities. Thus filtered-arm priority sensitivity is negligible here; not evidence of ranking skill.

**Decision**: Do NOT promote combined score. In recovery it only narrowly exceeds symbol_desc (€1.97) and has no independent test; in breakout it underperforms symbol_asc by €1056.91. Outcomes are descriptive and priority variants share a previously inspected dataset. No confidence intervals, matched risk, MTM drawdown, execution validation or independent OOS score evaluation. The first-pass replay was executed locally from the archived candidate audit using the inspected simulator logic; GitHub CI for the newly added module was queued at time of inspection. Do not mislabel these as CI-confirmed module results.

Next: independently confirm replay from the actual checked-in code in GitHub Actions; assess concentration, sector and opportunity cost and a fresh chronological holdout before choosing a ranking policy.
