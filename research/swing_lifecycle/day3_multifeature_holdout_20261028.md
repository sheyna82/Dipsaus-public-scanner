# Four-feature day-3 exit duration holdout — 2026-10-28

Research-only; do not deploy. No production or main changes.

Reproduced local analysis: /mnt/data/dipsaus_day3_multifeature_holdout.py. Inputs: actual holding paths and next-open dynamic exit trades. Features observed by day 3: close return, worst low, best high, log10 prior liquidity. Training signal dates before Aug 1 with 15-day exit date strictly before Aug 1 (purge). Forward signals Aug 1 onward. Tree depth 2, min leaf 250, training delta clipped to 1st/99th percentiles; choose 10 sessions only when model predicts >1 pp extra return, else 5. No forward outcomes used for fitting.

Purged train n=2,274: fixed5 mean +0.347%, fixed10 +2.731%, day3 simple +0.548%, tree +2.122%.
Forward n=2,272: fixed5 mean +0.140%, fixed10 -0.302%, day3 simple +0.348%, tree -0.315%. Tree selected 10 sessions for 34.73%; its loss >=5% rate 24.82% versus fixed5 19.89%. Tree minus fixed5 paired mean -0.455 pp; ticker-cluster bootstrap 95% [-0.675,-0.211]. Paired winsorized delta -0.523 pp. Simple day3 rule paired mean +0.208 pp but winsorized -0.001 pp and bootstrap interval [-0.100,+0.583] includes zero.

**Interpretation:** four-feature tree fails to generalize, should not deploy. This is NOT a pristine untouched holdout because the same Aug–Oct window has been examined in previous iterations; treat as exploratory falsification, not definitive inference. Ticker-only clustering fails to capture common market-day dependencies. Costs are illustrative; no bid/ask, FX, earnings point-in-time data, portfolio capital, or true execution simulation. Do not use these results as proof five days is universally optimal.

Next: freeze candidate rule definitions, validate on a genuinely later or previously untouched historical period, group by ticker and date, regime features known at decision time, model missed upside and drawdown, plus realistic portfolio opportunity costs.
