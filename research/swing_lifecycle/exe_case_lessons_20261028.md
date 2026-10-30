# EXE swing postmortem — research only (2026-10-28)

No personal identifying details, account data, order IDs, or private broker records. User-supplied executed prices, illustrative case only; not a historical predictive validation.

## Trade chronology
- 2026-08-26: buy 37 at USD 97.00 = USD 3,589.00.
- 2026-08-31: buy 30 at USD 99.37 = USD 2,981.10.
- 2026-10-01: buy 47 at USD 86.00 = USD 4,042.00.
- 2026-10-28: sell 114 at USD 92.10 = USD 10,499.40.
- Total buys USD 10,612.10; price-only realized difference USD -112.70 (-1.062% of purchases). Fees, FX and net EUR realized P&L require broker reconciliation.
- 63 calendar days from first entry to final exit, far beyond desired 5–15 trading-day recovery swing. Later purchases do not reset original position age.

## Findings / hypotheses, not causal conclusions
1. Averages and FX can make an underwater stock look recovered: separate price P&L from FX P&L and per-tranche outcomes.
2. Averaging down can reduce cost basis but increase capital-at-risk and time exposure. Each add must pass an independent standalone entry thesis and portfolio risk budget.
3. Absence of documented time-based review can permit unintended long holds; day 3/5/10/15 decision checkpoints, with explicit extension justification.
4. Earnings exposure requires proactive, timestamped risk review before report and monitoring of price/volume reaction after.
5. A sell limit above the bid does not guarantee execution or preserve P&L. Execution and remaining position quantity must be verified.
6. Avoid hindsight: cannot infer that earlier exits would have been better without point-in-time price paths, events and fills.

## Proposed research gates
- Entry record: source freshness, independent setup, target, invalidation, event calendar, position/sector exposure, FX, friction and expected time-to-target.
- Add record: independent expected return/risk, no rescue averaging, preserve original trade age, aggregate exposure cap.
- Hold checkpoints: 3/5/10/15 trading days; if thesis deteriorates, mandatory human EXIT/REDUCE/HOLD_WITH_REASON decision.
- Profit buffer: EUR net P&L and separate product/FX components, MFE and giveback alerts; not automatic liquidation.
- Event gate: advance earnings calendar warning and explicit manual hold-through decision.
- Research: chronological out-of-sample, broad liquid EU/US universe, matched baselines, realistic bid/ask costs, FX, overlapping positions, MAE/MFE, time-in-trade, downside tails, false alarms, forgone upside.
- Never auto-order or merge to main without explicit approval. Research-only until validated.
