# Historical feature formula reproduction — 2026-11-09

Research-only, trade_ready=false.

Independently recalculated **all 916** archived candidate rows (278 breakout, 638 recovery) using the original source snapshot in historical GitHub Actions artifact **13428010951**. All **916/916** match **all three** published archived feature values to 4 decimal places (absolute tolerance 0.000051). Zero mismatches.

Recovered formulae from numerical reproduction (the original feature-generator source code was not yet inspected):
- `relative_strength_20d_pct = 100 * (stock_close[t]/stock_close[t-20]-1) - 100 * (SPY_close[t]/SPY_close[t-20]-1)`. This is stock 20-session return **minus SPY** 20-session return, not stock return alone.
- `volume_ratio_20d = volume[t] / mean(volume[t-20:t])`; exclude signal day's volume from baseline.
- `atr_14_pct = 100 * mean(TR[t-13:t+1]) / stock_close[t]`; `TR[t] = max(high-low, abs(high-prev_close), abs(low-prev_close))`; simple arithmetic mean, **not Wilder smoothing**.

Source ZIP SHA256: `10a99a373e1d054267c4053c8f9dfb9315dbf28789d7dc5e1763c5faba6ea82a`.

**Critical correction to previous AMD November check:** The prior 2026-11-06 AMD-only calculation used stock 20-session return, not SPY-relative strength. Its `relative_strength_20d_pct` value is **not valid as an official frozen-protocol feature**. No contemporaneous SPY 2026 bars are included in the AMD-only captured artifact; official November AMD relative strength remains **BLOCKED_PENDING_SPY_DATA**. Do not treat the earlier 2/3 failure as a completed protocol verdict. Volume and ATR calculations require ongoing provenance/time-alignment verification.

Prospective protocol begins 2026-11-07; the AMD capture ends 2026-11-06. There is **no new prospectively eligible AMD signal** in that capture. Do not backdate one.

No operational scanner changes, no main changes, no orders, no stoploss/stoplimit.
