# DIPSAUS — first price-based walk-forward pilot, 2026-10-27

**Research only; NO-GO for strategy promotion.** Input: GitHub Actions artifact 12739376023, 18 US equities, 1,255 common sessions (unverified OHLC). This pilot tests **four**, not all 17 ranking strategies. It measures per-symbol trade outcomes, **not** a six-position portfolio or matched benchmark. The source and adjustment conventions remain unverified.

Algorithm: a signal is a >=10% drop from the trailing 20-close maximum. Compare dip-only, dip+close above 5-close mean, dip+one positive close, dip+two consecutive positive closes. Enter next-session open, exit at open after 5, 10, or 15 sessions; subtract 50bps round trip. Training is expanding with minimum 504 common sessions, then a 20-session purge, then 126-session validation, stepping 126 sessions, producing 5 validation folds. The training strategy with highest mean net return among candidates with >=20 nonoverlapping per-symbol trades is selected; validation outcomes do not enter selection. Within each fold and candidate, same-symbol trades are filtered to nonoverlapping intervals. No lookahead in these price-only signal definitions.

| Holding sessions | Training-selected candidate across five folds | Positive validation folds | Validation mean net return by fold (%) | Validation trades by fold |
|---|---|---:|---|---|
| 5 | one positive close | 1/5 | -0.3794, -0.3272, -0.4815, +2.2257, -0.0145 | 15, 25, 48, 8, 27 |
| 10 | dip only | 5/5 | +0.3697, +2.0714, +0.2824, +0.0338, +1.9610 | 15, 23, 48, 11, 31 |
| 15 | dip only | 3/5 | -0.5999, +1.5505, +1.6453, -0.4181, +2.6710 | 14, 17, 39, 7, 27 |

**Cautions:** this is an exploratory retrospective walk-forward; the hypotheses were already explored on the data and are not fully unseen. The five fold means are correlated by shared training histories and by common market/sector shocks. A 10-day signal with 5/5 positive folds is promising only as a *research lead*. Per-trade means do not imply net portfolio profits. The simple implementation does not model six-slot capital constraints, FX, dividends, liquidity, borrow, corporate actions, missing/delisted stocks, or exposure-matched index comparisons. The source archive is unverified. Trade entry/exit are based on unadjusted provided OHLC without independently confirmed split handling.

Next: add the 17 ranking methods using a common, deterministic six-slot daily portfolio accounting engine; pre-register the selection metric; test purged rolling folds and reserve new unseen market data. Reconcile previous simulation discrepancies, and verify source licensing/provenance. No merge to main or auto-orders.
