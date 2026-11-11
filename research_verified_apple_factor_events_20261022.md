# Observed AAPL adjustment factors — verified 2026-10-22

GitHub Actions: https://github.com/sheyna82/Dipsaus-public-scanner/actions/runs/39757079682
Job observed-apple-adjustment-factors (119751690386): **success**.

Real public Apple sample (2015-02-17 to 2017-02-16), 506 trading sessions:
- adjusted-close / ordinary-close factor min: 0.9614742329562933
- max: 1.0
- eight changes above 0.1%:
  2015-05-07, 2015-08-06, 2015-11-05,
  2016-02-04, 2016-05-05, 2016-08-04,
  2016-11-03, 2017-02-09.

Quarterly cadence is consistent with dividend adjustment events but
**event type has not been independently verified**. This result does not
establish which feed's OHLC values are adjusted, or whether the SPY feed
uses identical conventions.

**Methodological decision:** do not naively substitute adjusted close
for close while leaving open/high/low unadjusted. Before a revised
evaluation, obtain a documented, consistent adjustment policy and
apply it to all required price fields, with corporate-action dates
checked independently. Keep adjustment validation blocked and all
results research-only. No live scanner changes.
