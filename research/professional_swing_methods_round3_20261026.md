# Professional swing trading research — round 3 (2026-10-26)

Research-only. Extends research/professional_swing_methods_expansion_20261026.md; no production changes.

## New methods to investigate
1. **Setup taxonomy**: trend pullback, breakout/volatility contraction, mean reversion after exhaustion, catalyst/event continuation. Evaluate each separately before blending; avoid assuming a single indicator works for all regimes.
2. **Trade thesis invalidation**: record ex-ante why a trade would cease to be attractive, even when no automatic stoploss is placed. Escalating risk alerts; do not misrepresent an alert as loss protection.
3. **Market exposure throttle**: vary total invested capital and number of concurrent positions in stressed/bearish conditions; distinguish improved drawdown from lower gross returns.
4. **Correlation and concentration budget**: six positions in one sector can behave like one leveraged sector bet. Measure pairwise correlations, sector and factor exposure; test limits without lookahead.
5. **Volatility contraction and volume confirmation**: research breakout follow-through versus false breakout, with OHLCV-derived features available at signal time.
6. **Failed breakout / no follow-through**: time-to-confirmation and time-stop versus fixed hold; study dead capital and opportunity cost.
7. **Earnings/event protocol**: separate ordinary swing and event-risk swing. Explicit overnight gap exposure, adjusted size and holding constraints; no assumption all events are predictable.
8. **Portfolio heat / worst-case stress**: gap shock and clustered drawdown simulations, including without stop orders.
9. **Execution quality**: bid-ask spread, market open gaps, liquidity, slippage, unfilled limit orders and FX for EUR accounts.
10. **Review discipline**: pre-trade written thesis, post-trade attribution, missed-signal tracking and separate diagnostics by setup/regime.

## Sources consulted
- Charles Schwab (2026-08-11), What Is Swing Trading and How Does It Work?: https://www.schwab.com/learn/story/swing-trading-strategies
- Charles Schwab (2024-10-23), Elements of a Smart Trade Plan: https://www.schwab.com/learn/story/5-elements-smart-trade-plan
- Charles Schwab (2025-03-07), The Ins and Outs of a Swing Trade: https://www.schwab.com/learn/story/ins-and-outs-swing-trade
- Investors.com (2026-10), SwingTrader TEAM exit case: https://www.investors.com/research/swing-trading/atlassian-swing-trade-why-we-sold-a-resilient-stock-in-a-tech-pullback/

## Testing order
A. Implement ex-ante trade thesis, invalidation and setup categories in offline diagnostics.
B. Compare risk-adjusted and net-dollar outcomes for regime-aware exposure and correlated positions against constant-exposure baseline.
C. Test failed-breakout/time-stop and volatility contraction on independently held-out real OHLCV.
D. Only then evaluate position scaling, partial exits and longer dynamic holds, guarding multiple-testing bias.

## Invariants
No broker actions, no changes to main or production notifications, no stoploss requirement, no changes to frozen protocol. No performance claims before independent out-of-sample validation.
