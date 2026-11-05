# Historical artifact inspection — actual ZIP contents (2026-11-03)

Source: GitHub Actions run `41121367948`, artifact ID `13007728223`, `candidate-feature-oos-historical-report` (downloaded and inspected, not inferred from filename).

ZIP members:
- `candidate_feature_oos.json` (217401 uncompressed bytes): research-only OOS report, 32 candidates; method `TRAINING_MEDIAN_ALL_THREE_FEATURES_OUT_OF_SAMPLE`.
- `candidate_feature_portfolio_quarters.json` (7477 bytes): quarterly portfolio analysis.
- `candidate_feature_oos_input_snapshot.json` (3887285 bytes): `DIPSAUS_OOS_OHLCV_V1`, 21 stock symbols plus SPY benchmark, 1255 bars per symbol.

**Observed timestamp cadence**: AMD and SPY each have 1255 distinct UTC dates from 2021-11-01 through 2026-10-30; median and minimum adjacent timestamp difference both 24 hours. Therefore these are **daily**, not 1-minute, bars. Never feed this snapshot to the intraday setup episode detector.

**Reproducibility verification**: independently recomputed SHA256 of sorted-key compact canonical JSON for each of the 21 stock bar arrays; all 21 match `candidate_feature_oos.json.input_data_provenance.stocks[*].sha256`. SPY benchmark hash also matches. These checks prove consistency of archived data and report, not market data authenticity.

**Declared report limitations**: convenience universe and correlated events; median feature filters are hypotheses, not validated alpha; Yahoo unadjusted OHLCV and SPY without corporate-action audit; no sector/event controls or broker execution evidence.

**Research decision**: reuse this snapshot for daily 5–15-session strategy/portfolio studies. Do not relabel it as intraday history or use it to claim independently verified intraday episode precision/recall. Continue separate, provenance-controlled acquisition of historical minute bars and independent episode labels. No live scanner or alert changes.
