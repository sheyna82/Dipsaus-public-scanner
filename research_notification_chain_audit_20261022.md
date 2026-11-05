# Scanner-wide notification chain: source-code findings (research only)

Reviewed: `.github/workflows/shadow-prealert.yml`, `shadow-eu.yml`,
`shadow-us.yml`, `safe_runner.py`, `private_notifications.py`.

- PRE-ALERT is scheduled in five-minute increments. Its scheduled path
  configures notifications enabled; manual dispatch defaults to read-only.
- EU and US recovery workflows explicitly set notifications disabled.
  They may still generate internal candidate and risk research.
- `safe_runner.notification_diagnostics` already records aggregate US/EU
  candidate and filter reasons; these categories do not cover every later
  deduplication, delivery, or receipt stage.
- `private_notifications.reserve_send` persists `reserved`, `rejected`,
  `uncertain`, and `sent` statuses. `sent` means the provider returned
  success, **not** that a device displayed the message.
- Daily deduplication and an early US global cap of three can intentionally
  suppress otherwise qualifying candidate notifications.
- The US automatic discovery path requires notification eligibility, fresh
  provider data, structural evidence and (for later prealerts) intraday hold
  confirmation. Fail-closed filtering can suppress alerts even with market
  movement.
- The current static review does **not** establish how many candidates passed
  each gate in actual private runtime or whether any phone received alerts.

Next: derive comparable aggregate funnel counts from permitted private
runtime evidence, with no ticker or portfolio identifiers, and audit actual
delivery acknowledgments only if an authorized channel supports them.
Do not treat a 2xx ntfy HTTP response as device acknowledgment. No changes
to live thresholds, notifications, or sender ownership.
