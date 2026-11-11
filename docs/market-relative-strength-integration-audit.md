# DIPSAUS market regime and relative-strength integration audit (research only)

Scope: read-only comparison against public stock-screener and quantitative research design ideas. No external code imported. No production wiring, trade clearance, notification or stop-loss changes.

## Existing code evidence

| Capability | Existing location | Verified in code | Gap |
|---|---|---|---|
| Market-regime research gate | `dipsaus_unified_research.py` | Gate exists; missing/stale evidence is UNKNOWN | No upstream producer proven connected |
| Relative-strength research gate | `dipsaus_unified_research.py` | Gate exists; missing/stale evidence is UNKNOWN | No benchmark-relative scoring producer proven connected |
| Broad-market headline confirmation | `macro_market_confirmation.py` | Requires macro headlines plus fresh SPY and QQQ quotes; research-only | Not a general market-regime measure; no breadth or trend evaluation |
| US recovery discovery | `us_momentum_recovery_discovery.py` | Broad Nasdaq-listed universe, liquidity and recovery gates, intraday structure | No explicit SPY-relative strength score or market-regime classification in candidate record |
| Historical outcome evaluation | Separate draft PR #59 | Offline outcomes, provenance declarations and cohort coverage | No verified historical signal feed or unbiased performance evidence |

## What to learn, not copy

- RyanJHamby stock-screener: market-regime context, relative strength and caching; its confirmed-uptrend breakout and stop-loss approach is **not** DIPSAUS recovery swing policy.
- Qlib: strict out-of-sample signal comparisons and data provenance; its full ML stack is not justified for current scope.
- Backtrader/Freqtrade/NautilusTrader: backtesting and execution realism principles; no dependency or licensed code imported.

## Next isolated research experiments

1. **Market regime:** define offline inputs for SPY and QQQ daily closes and a broad-market breadth measure, with dated source/provenance and explicit UNKNOWN on absent or stale data. Avoid interpreting two positive intraday index changes as proof of an uptrend.
2. **Relative strength:** compare each candidate's returns to the same-session benchmark over fixed 5/20-session windows; require aligned trading sessions, adjustment basis and currency handling. Separate absolute recovery from benchmark outperformance.
3. **Nonblocking discovery:** measure candidate retention with and without regime/relative-strength context; never silently reject recovery candidates because context is UNKNOWN.
4. **Bias audit:** compare historical nominated cohort counts, missing data and subsequent outcomes (PR #59), including negative/failed candidates. Avoid selection based only on today's survivors.
5. **Acceptance:** offline unit tests and shadow-only reports first. Require explicit user approval before connecting live alert paths.

## Current conclusion

The principal gap is **integration and trustworthy upstream evidence**, not absence of gate names. A research label is not an executable buy/sell signal. No claim of profitable improvement is supported yet.
