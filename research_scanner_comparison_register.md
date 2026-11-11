# DIPSAUS — comparative scanner research register (2026-10-22)

**Scope:** offline research only. No live alerts, orders, portfolio data, credentials or stop-loss defaults change. External repositories are sources of ideas, not verified sources of profitable signals. Check upstream licenses before copying any code; prefer independent implementations.

| Reference | Multiple transferable ideas | DIPSAUS experiment | Evidence gate |
|---|---|---|---|
| QuantConnect LEAN | event-driven order simulation; slippage/fees; corporate-action handling; backtest/live consistency | replay frozen signals with next-session execution, fees and delayed data | verify fill assumptions, split/dividend handling, reproducible results |
| Microsoft Qlib | point-in-time feature pipeline; rank-based prediction; rolling evaluation; dataset discipline | compare simple frozen technical rule with rank-only relative-strength candidate | leakage audit, chronological untouched data, baseline comparison |
| Freqtrade | lookahead analysis; recursive indicator checks; dry-run; strategy comparison; notification observability | automated lookahead invariance tests and simulated alert delivery | any leakage or failed alert => blocked |
| PyBroker | walk-forward splits; feature/model evaluation; significance and execution | rolling evaluation with purge/embargo and pre-registered metrics | per-ticker and regime sufficiency, no optimization on test |
| RDT Trading System (niickyg) | SPY-relative strength; ATR normalization; daily trend filter; intraday entry timing; semi-automated alerts | isolate RS/ATR factor from frozen rule; test incremental value, not combined kitchen-sink | compare identical ticker/date cohorts; fees and adverse excursion |
| vectorbt | rapid vectorized factor sweeps; sensitivity and robustness | run exploratory sensitivity ONLY on training cohort | never select hyperparameters on evaluation cohort |
| NautilusTrader | event-driven replay; latency/order lifecycle; unified simulation | examine delayed/missed alert handling before integration | idempotency, traceability and failure tests |
| OpenBB / finvizfinance | fundamental screens, filings and cross-source retrieval | evaluate earnings/calendar/sector exclusions with as-of timestamps | source licensing and point-in-time verification |
| stomar | regime classifier; cross-sectional ranking; drift checks; consensus | compare separate market-regime strata, avoid fitting consensus until factor tests pass | no claims without independently tested incremental value |

## Candidate experiments (priority)
1. **Lookahead and leakage audit**: perturb all future bars while preserving earlier bars; historical signals before perturbation MUST remain identical. Assert earnings calendar availability timestamps and prevent adjusted-close future leakage.
2. **RS/ATR experiment**: calculate contemporaneously observable stock-vs-SPY relative strength, normalize by ATR, and compare with frozen technical rule. Report trade count, net excess return, severe adverse excursion, overlap and lost opportunities.
3. **Market-regime stratification**: split bullish/bearish/high-volatility periods using only prior-session data; descriptive only until each group is sufficiently populated.
4. **Event-aware safety**: earnings, macro releases, splits and source outages; prioritize verified as-of data.
5. **Notification reliability**: test full detection → dedupe → transport → acknowledged receipt path. CI green is not proof that the user received a message.
6. **Execution realism**: next open, spread, fees, missing data, halted securities, corporate actions.
7. **Cross-sectional ranking and model drift**: only after clean point-in-time data and leakage tests.

## Rules
- Freeze each hypothesis, formula, ticker universe, benchmark, time split and minimum sample before viewing the test.
- Evaluate incremental benefit against the current frozen rule on the **same** dates/universe; use independent holdout and account for multiple comparisons.
- Measure *both* expected excess return and maximum intraperiod adverse excursion. Do not replace a weak edge with a pretty composite score.
- Prefer a small number of reliable, interpretable signals to indicator stacking.
- Do not automatically place stop-losses or orders. Manual decision support only.
- Status remains **EXPLORATORY / DATA_BLOCKED** where source provenance, survivorship, earnings as-of, corporate actions, or sample size are unverified.

## Source links
- https://github.com/QuantConnect/Lean
- https://github.com/microsoft/qlib
- https://github.com/freqtrade/freqtrade
- https://github.com/edtechre/pybroker
- https://github.com/niickyg/rdt-trading-system
- https://github.com/polakowo/vectorbt
- https://github.com/nautechsystems/nautilus_trader
- https://github.com/OpenBB-finance/OpenBB
- https://github.com/uttampaliwal/stomar
