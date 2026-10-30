# First independently reproduced observed-price pilot — 2026-10-22

GitHub Actions run: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39749391086
Job: observed-price-pilot (119725833230), conclusion: success.

The actual Python research runner downloaded 506 AAPL daily observations
(2015-02-17 to 2017-02-16) from Plotly's public example dataset and
executed the local price-history evaluation. The separate unit-test job
also passed.

**Verbatim values from GitHub job log:**
- observations: 44
- selected_count: 26
- selected_mean_net_pct: 0.16822446153846157
- all_entry_mean_net_pct: -0.10875622727272728
- benchmark: AAPL itself (invalid as independent benchmark)
- reproducibility_only: true

These match the prior separate JavaScript exploration to rounding.
They are NOT evidence of statistically significant predictive value.
AAPL was its own benchmark, no real historical earnings calendar,
survivorship handling, independent universe, point-in-time vendor
verification, spread/slippage or out-of-sample holdout. The 10 bps
per-side fee is an assumption, not observed execution data.

**Next priority:** obtain an independent benchmark aligned to the same
sessions, audit its price adjustments, and test multiple symbols across
chronological development/holdout windows. Do not promote to live alerts.
