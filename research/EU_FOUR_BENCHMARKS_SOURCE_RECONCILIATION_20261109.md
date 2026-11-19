# EU official benchmark crosswalk — 2026-11-09, independent source check

Research only; **provider validation and signal eligibility remain BLOCKED**.

| Benchmark | Official price index | Official ISIN | Official reference |
|---|---|---|---|
| Amsterdam | AEX | NL0000000107 | Euronext compliance list: https://live.euronext.com/sites/default/files/documentation/index-rules/Compliance%20Statement%20Euronext%20Amsterdam_0.pdf |
| Frankfurt | DAXK (DAX price index) | DE0008467440 | STOXX DAX factsheet https://stoxx.com/index/dax/?factsheet=true |
| Helsinki | OMXH25 (capitalization-weighted stock price index, EUR) | **ISIN not independently established** | Nasdaq official https://indexes.nasdaqomx.com/index/overview/omxh25 |
| Europe | SXXP (STOXX Europe 600 price, EUR) | EU0009658202 | STOXX factsheet https://stoxx.com/index/SXXP/?factsheet=true |

## Critical source discrepancy — Helsinki

At time of research, Nasdaq's official OMXH25 overview displays **2026-11-06 = 6188.75** while FRED's Nasdaq-sourced daily series **NASDAQOMXH25** displays **2026-11-06 = 6221.79**. Sources:
- https://indexes.nasdaqomx.com/index/overview/omxh25
- https://fred.stlouisfed.org/series/NASDAQOMXH25

The **33.04 index-point disagreement** is not resolved. Possible reasons (index version, timing, revisions, vendor metadata) are hypotheses, not verified explanations. **Block NOKIA.HE relative-strength qualification** pending independent reconciliation of index version and timestamp. Do not pick the more convenient value.

## Remaining independent verification

1. Confirm the Yahoo symbols `^AEX`, `^GDAXIP`, `^OMXH25`, `^STOXX` map to the *exact* official price indices above, rather than similarly named performance variants.
2. Capture 6-month daily OHLCV/close series and hashes; compare provider metadata and multiple date-specific close observations with official sources.
3. Confirm benchmark close timestamps, local trading calendar, and exclude current incomplete bar.
4. Then execute the aligned 20-session relative strength comparison; no unapproved European threshold, trade or main/live modification.

Current `research_capture_europe_benchmarks.py` deliberately marks `benchmark_identity_verified=false`. Successful download alone must not override this gate.
