# DIPSAUS — raw historical data availability checkpoint (2026-11-05)

## Inspected, concrete evidence

- Historical workflow run [40316862372](https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/40316862372) is confirmed completed successfully, head commit `827cdcb19197f8d0340b5434780705cb9e695f4b` on historical research branch.
- The GitHub Actions artifacts listing for that **specific run** currently returns `{"total_count":0,"artifacts":[]}`. Thus artifact `12647277768` referenced by the historical dynamic-exit report is **not presently retrievable through this run's artifact listing**. This does not prove it never existed; it may have expired or been removed.
- Historical branch `research/offline-technical-risk-20261021` tree was enumerated (926 entries, not truncated). It includes code to fetch and evaluate provider OHLCV, historical reports and some limited event observation CSV files. A repository path or workflow script is **not** proof that its original 96-trade raw ledger is present.
- `research/first_real_dynamic_exit_comparison_20261026.md` explicitly describes 96 hypothetical entry moments, AMD/COHU/META/SPY, 24 per symbol, entry and exit at opening prices, 10 bps per side, and aggregate variant totals. Its source notes that quotes are not independently validated and these are **not** six-position portfolio returns.
- `research/candidate_feature_oos.py` and `research/candidate_portfolio_capacity.py` already implement held-out candidate selection and chronological capacity accounting. Prefer auditing/reusing those over constructing another incompatible historical engine.
- `research/HISTORICAL_DATA_SOURCE_DUE_DILIGENCE_20261023.md` identifies licensing, corporate-action, timestamp and survivorship caveats; no blanket right to republish provider raw OHLCV.

## Reconciliation status

`RAW_96_TRADE_LEDGER_NOT_VERIFIED`: aggregate report located, original per-entry source data not verified or retrieved. Historical aggregate P&L must **not** be fed as if it were independent per-trade returns. No capital-sizing performance comparison can be honestly claimed from those totals alone.

## Next defensible step

1. Locate an accessible, license-compliant existing provider archive or reproducible source snapshot, with SHA256 and source metadata; do not silently reacquire changed data and call it the original sample.
2. If an original immutable source cannot be recovered, classify a newly acquired dataset as a **new experiment**, preregister its hypothesis and calendar/FX/corporate-action policies, and maintain an untouched holdout.
3. Audit the older capacity engine's entry/exit event ordering against the newer settlement and cashflow research modules, including holiday coverage and same-symbol overlap.
4. Export only reproducible aggregate metrics or safe manifests to the public branch; do not commit raw broker/account data or licensed market rows.

**No live scanner, main, broker, portfolio, order or position sizing change.**
