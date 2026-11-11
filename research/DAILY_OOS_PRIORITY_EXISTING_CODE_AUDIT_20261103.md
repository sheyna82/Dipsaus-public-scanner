# Capacity-priority audit — existing functionality and next evidence gate

Date: 2026-11-03. Read-only code inventory of `research/candidate_feature_oos.py` and `research/candidate_portfolio_capacity.py`.

**Do not rebuild** neutral priority comparisons: `candidate_feature_oos.py` already simulates `symbol_asc`, `symbol_desc` and `stable_hash` on the same dated baseline/filtered candidate pools, records candidate-level accept/reject reasons and capital occupancy, and reports return range. `candidate_portfolio_capacity.simulate` already supports `score_desc` but requires each event to contain a finite score.

**Critical distinction**: existing neutral tie-breaks diagnose capacity selection instability. They do not rank by ex-ante opportunity quality. Never select whichever neutral ordering had highest test-period PnL: that is in-sample optimization.

**Next valid experiment, only after inspecting existing feature scoring code**:
1. Identify an existing score whose input data is available strictly at signal close, before next-open entry; explicitly audit timestamp and missing-data behavior.
2. Use the *same* frozen baseline event pool and identical max six positions, €3,500 tranche, 10-session exits, fees and date split. Compare predeclared `score_desc` with neutral priority scenarios; avoid scoring with net_return_pct or other realized outcomes.
3. Validate no lookahead, no changed event universe, deterministic ties and full accepted/rejected ledger reconciliation. Missing scores must fail closed, not silently become zero.
4. Compare capital-calendar-days, capital-session-days on independently verified trading calendar, paired missed-opportunity PnL, turnover, sector concentration, quarterly stability and clustered uncertainty.
5. Promote only with held-out evidence and independent execution/corporate-action checks; all current outputs research-only.

No main merge, private scanner, alerts, cron or trading changes.
