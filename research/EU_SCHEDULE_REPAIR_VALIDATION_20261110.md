# EU schedule repair — validation and deployment boundary (2026-11-10)

## Incident evidence

- Existing operational workflow: `.github/workflows/shadow-eu.yml` on `main`, commit `3f99da230a7f91c0bb361a57d7fa3654ad1f8325`.
- Configured local-time schedule was not reflected by observed scheduled-run cadence. GitHub scheduled-run history for 2026-11-05, 06, 09, 10 contained respectively 4, 5, 3, 1 EU runs (2026-11-10 partial day). This is an observation, not proof of the scheduler's root cause.
- Scheduled run `42742222012` (run #245) failed on `europe_ohlcv_pilot.py`: 151 attempted, 147 passed structural checks, 0 fresh-verified, 147 stale, last reported date 2026-11-06, and zero reported HTTP/URL/timeout errors. Fail-closed behavior was correct.
- Manual EU run `42789034517` (run #246) succeeded with 151 attempted, 147 fresh-verified, 0 stale and `EU_HANDOFF_POSTSAVE: FRESH`. This verifies manual execution, not scheduled execution.

## Isolated candidate repair

- Research-branch commit `543f7a644abcc47e9d37fa66c7426f6982252d07` changes only the EU workflow schedule to explicit UTC cron `2,17,32,47 6-17 * * 1-5`, avoiding whole-hour scheduling. This is a 15-minute cadence within the UTC window, not a 5-minute cadence.
- The UTC window intentionally covers both CET and CEST European cash hours, but extends outside those hours; execution must continue to honor any applicable market-session and freshness gates. The configuration does not independently prove those gates.
- All nine commit-specific research workflows completed successfully: `42821440514`, `42821440542`, `42821440583`, `42821440730`, `42821440595`, `42821440509`, `42821440564`, `42821440529`, `42821426823`. These are CI results, not live schedule observations.

## Release gate — NOT SATISFIED

- No scheduled run can validate the research-branch cron before it reaches the default branch. Do not claim the scheduler is repaired in production.
- The precise root cause of missing GitHub scheduled events remains unproven; GitHub Actions schedule execution is not guaranteed at exact times.
- Before any separately authorized live deployment: verify desired cadence and time window, explicit UTC/DST behavior, duplicate/concurrency policy, market-session gating, data-provider quota impact, and rollback plan. Do not merge draft PR #65 as a shortcut.
- After any separately authorized deployment: compare scheduled trigger times and actual run starts for at least one full European session, measure gaps and data freshness, and ensure PRE-ALERT receives fresh EU handoffs. A green job alone is insufficient.
- No changes to `main`, no live-scanner modification, no merge, no trading order.
