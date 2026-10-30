# Verified AAPL/SPY price adjustment sensitivity — 2026-10-22

GitHub Actions run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39760030458
Adjustment-sensitivity job 119761615262: success.

Observed results (44 non-overlapping 10-session observations):

| Metric | Raw AAPL OHLC | AAPL OHLC rescaled by AdjClose/Close |
| --- | ---: | ---: |
| Selected count | 22 | 22 |
| Selected mean net (%) | +0.0916068181818182 | +0.1539375 |
| All-entry mean net (%) | -0.10875622727272728 | -0.01976856818181816 |

This **does not** validate the strategy. The selected mean changed by
+0.0623306818181818 percentage points while the all-entry mean changed
by +0.08898765909090912 percentage points. Thus the difference
(selected minus all-entry mean) actually *decreased* from about
+0.20036 to +0.17371 percentage points. Selection count equality
does not establish the same selected dates; compare dates explicitly.

Adjustment policies for Apple and SPY are not independently verified.
No historical earnings calendar, out-of-sample holdout, confidence
interval, corporate-action verification or execution validation.
Do not treat adjusted scenario as a validated return series and do not
promote to live alerts.
