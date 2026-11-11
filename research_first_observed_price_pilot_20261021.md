# First observed-price exploratory calculation — AAPL 2015–2017

Date of research: 2026-10-21. No live scanner changes.

## Source
Public example dataset `plotly/datasets/finance-charts-apple.csv` on GitHub,
read using the GitHub connector (506 rows, 2015-02-17 through 2017-02-16).
This is an example visualization dataset, not an independently audited
point-in-time research feed. No third-party price bars are copied into this repo.

## Exploratory calculation (separate in-memory JavaScript calculation)

44 non-overlapping evaluation windows starting after 21 daily bars.
Signal after close, hypothetical entry next open, exit close 10 sessions
after entry, subtract 10 basis points each side.

A price-only proxy for the heuristic baseline scored each signal.
Because an independent benchmark was unavailable, stock was effectively
its own benchmark: relative strength contribution = 1 and market context
was computed using the same stock. **This is a compromised baseline**,
not the intended stock-vs-market comparison. Earnings risk was not
checked. Selection threshold >=5 points.

- 44 evaluated entry dates.
- 26 selected by price-only proxy.
- Selected mean net 10-session return: +0.1682245%.
- All-entry mean net 10-session return: -0.1087562%.

## Critical limitations
These are **not GitHub CI backtest results**; calculations were performed
separately in memory and have not been independently reproduced against
the Python research evaluator. No benchmark, verified release timestamps,
earnings dates, delisted-stock universe, slippage, spreads, market impact,
out-of-sample split or uncertainty intervals. Apple alone, from a
survivor-only example dataset, cannot establish predictive skill.
Selection bias and small sample are severe. Do not trade on this result.

## Next verification
Use the same bars in the Python research evaluator without committing
them to the public repository, then compare to a separately sourced
historical benchmark and report a chronological holdout. Record data
license and adjustments before presenting performance as validated.
